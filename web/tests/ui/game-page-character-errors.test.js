import test from "node:test";
import assert from "node:assert/strict";

import { ApiError } from "../../src/adapters/api/api-error.js";
import { GamePage } from "../../src/ui/pages/game-page.js";


function characterDocument() {
  const nodes = new Map([
    ["characterName", { value: "夜班調查員" }],
    ["characterBackground", { value: "熟悉所有交班紀錄。" }],
    ["characterTrait", { value: "冷靜" }],
    ["characterWeakness", { value: "多疑" }],
    ["courageInput", { value: "2" }],
    ["insightInput", { value: "1" }],
    ["bondInput", { value: "0" }],
  ]);
  return {
    nodes,
    documentRef: { getElementById: (id) => nodes.get(id) },
  };
}


async function saveCharacterWith(error) {
  const originalDocument = globalThis.document;
  const { nodes, documentRef } = characterDocument();
  globalThis.document = documentRef;
  try {
    const feedback = [];
    const busyStates = [];
    const canonicalRoom = {
      roomCode: "ABCD23",
      status: "LOBBY",
      version: 7,
      session: { isHost: false },
    };
    const page = new GamePage({
      updateCharacter: {
        async execute() {
          throw error;
        },
      },
    });
    page.room = canonicalRoom;
    page.setBusy = (busy) => busyStates.push(busy);
    page.showFeedback = (message, kind) => feedback.push({ message, kind });
    page.syncRoute = () => {};
    page.render = () => {};

    await page.handleCharacter({ preventDefault() {} });

    return { page, canonicalRoom, nodes, feedback, busyStates };
  } finally {
    globalThis.document = originalDocument;
  }
}


test("角色儲存遇到未知 JavaScript exception 時隱藏原文並保留輸入", async () => {
  const rawMessage = "Cannot read properties of undefined (reading 'character')";
  const result = await saveCharacterWith(new TypeError(rawMessage));
  const shownError = result.feedback.find(({ kind }) => kind === "error");

  assert.deepEqual(shownError, {
    message: "角色儲存失敗，請重新整理後再試。",
    kind: "error",
  });
  assert.doesNotMatch(shownError.message, /TypeError|Cannot read|undefined|character/i);
  assert.equal(result.page.room, result.canonicalRoom, "失敗不可覆寫 canonical room");
  assert.equal(result.nodes.get("characterName").value, "夜班調查員", "失敗不可清空角色輸入");
  assert.deepEqual(result.busyStates, [true, false], "失敗後必須解除 submitting 狀態");
});


test("角色儲存仍顯示已正規化的 ApiError 訊息", async () => {
  const result = await saveCharacterWith(
    new ApiError("CHARACTER_NOT_EDITABLE", "只有等待中的房間可以編輯角色。", 409),
  );
  const shownError = result.feedback.find(({ kind }) => kind === "error");

  assert.equal(shownError.message, "只有等待中的房間可以編輯角色。");
  assert.equal(result.page.room, result.canonicalRoom);
});
