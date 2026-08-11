import test from "node:test";
import assert from "node:assert/strict";

import { GamePage } from "../../src/ui/pages/game-page.js";

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
