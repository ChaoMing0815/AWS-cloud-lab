import test from "node:test";
import assert from "node:assert/strict";

import { GamePage } from "../../src/ui/pages/game-page.js";
import { ApiError } from "../../src/adapters/api/api-error.js";

test("GamePage 生成 canonical world draft 後留在 DRAFT 並回填可編輯欄位與剩餘次數", async () => {
  const originalDocument = globalThis.document;
  const nodes = new Map([
    ["worldKeywordsInput", { value: " 夜班,便利商店，盤點 " }],
    ["toneInput", { value: "mystery" }],
    ["customToneInput", { value: "" }],
    ["supplementalRequestInput", { value: " 讓玩家先編輯。 " }],
    ["worldTitle", { value: "" }],
    ["worldPremiseInput", { value: "" }],
    ["worldObjectiveInput", { value: "" }],
    ["openingSceneInput", { value: "" }],
    ["coreObstacleInput", { value: "" }],
    ["worldGenerationRemaining", { textContent: "" }],
  ]);
  globalThis.document = { getElementById: (id) => nodes.get(id) };
  try {
    let command;
    const canonicalDraft = {
      status: "DRAFT",
      version: 2,
      worldGenerationCount: 1,
      world: {
        storyTitle: "夜班盤點迷蹤",
        premise: "盤點資料在夜班期間離奇消失。",
        objective: "找回正確資料。",
        openingScene: "收銀機重啟後，交班紀錄全空白。",
        coreObstacle: "備份硬碟被鎖在倉庫。",
      },
    };
    const page = new GamePage({
      generateWorld: { async execute(received) { command = received; return canonicalDraft; } },
      navigate: () => { throw new Error("生成草稿不得切換至 Lobby"); },
    });
    page.room = { status: "DRAFT", version: 1, session: { isHost: true } };
    page.setBusy = () => {};
    page.showFeedback = () => {};
    page.syncRoute = () => {};
    page.render = () => {};

    assert.equal(typeof page.handleGenerateWorld, "function", "GamePage.handleGenerateWorld 尚未建立");
    await page.handleGenerateWorld({ preventDefault() {} });

    assert.deepEqual(command, {
      keywords: " 夜班,便利商店，盤點 ",
      tone: "mystery",
      customTone: "",
      supplementalRequest: " 讓玩家先編輯。 ",
    });
    assert.equal(page.room.status, "DRAFT");
    assert.equal(nodes.get("worldTitle").value, "夜班盤點迷蹤");
    assert.equal(nodes.get("worldPremiseInput").value, "盤點資料在夜班期間離奇消失。");
    assert.equal(nodes.get("worldGenerationRemaining").textContent, "剩餘 1 次生成");
  } finally {
    globalThis.document = originalDocument;
  }
});

test("GamePage 確認世界的 422 會標示對應欄位並保留可編輯草稿", async () => {
  const originalDocument = globalThis.document;
  const input = (value = "") => ({
    value,
    attributes: {},
    setAttribute(name, attributeValue) { this.attributes[name] = attributeValue; },
    removeAttribute(name) { delete this.attributes[name]; },
  });
  const nodes = new Map([
    ["worldTitle", input("夜班盤點迷蹤")],
    ["worldPremiseInput", input("太短")],
    ["worldObjectiveInput", input("找回正確資料。")],
    ["openingSceneInput", input("收銀機重啟後，所有交班紀錄都空白。")],
    ["coreObstacleInput", input("備份硬碟被鎖在倉庫。")],
    ["toneInput", input("mystery")],
    ["customToneInput", input("")],
    ["maxRoundsInput", input("6")],
    ["worldTitleError", { hidden: true, textContent: "" }],
    ["worldPremiseError", { hidden: true, textContent: "" }],
    ["worldObjectiveError", { hidden: true, textContent: "" }],
    ["openingSceneError", { hidden: true, textContent: "" }],
    ["coreObstacleError", { hidden: true, textContent: "" }],
  ]);
  globalThis.document = { getElementById: (id) => nodes.get(id) };
  try {
    const draftRoom = { status: "DRAFT", version: 2, session: { isHost: true } };
    const page = new GamePage({
      confirmWorld: {
        async execute() {
          throw new ApiError("REQUEST_VALIDATION_FAILED", "請檢查標示的欄位。", 422, {
            premise: "至少需要 50 個字元。",
          });
        },
      },
    });
    page.room = draftRoom;
    page.setBusy = () => {};
    page.showFeedback = () => {};
    page.syncRoute = () => {};
    page.render = () => {};

    await page.handleConfirmWorld({ preventDefault() {} });

    assert.equal(page.room, draftRoom, "驗證失敗不可覆寫現有草稿");
    assert.equal(nodes.get("worldPremiseInput").attributes["aria-invalid"], "true");
    assert.equal(nodes.get("worldPremiseError").hidden, false);
    assert.equal(nodes.get("worldPremiseError").textContent, "至少需要 50 個字元。");
    assert.equal(nodes.get("worldTitleError").hidden, true);
  } finally {
    globalThis.document = originalDocument;
  }
});
