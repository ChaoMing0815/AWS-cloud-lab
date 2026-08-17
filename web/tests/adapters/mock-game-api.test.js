import test from "node:test";
import assert from "node:assert/strict";

import { MockGameApi } from "../../src/adapters/api/mock-game-api.js";

const world = {
  storyTitle: "午夜便利商店大作戰",
  premise: "三位夜班夥伴發現年度盤點資料離奇消失，店長將在天亮前抵達並檢查紀錄。",
  objective: "在店長抵達前找回盤點資料。",
  openingScene: "凌晨兩點，收銀機突然重新開機，盤點檔案也消失了。",
  coreObstacle: "備份硬碟被鎖在倉庫裡。",
  tone: "slice_of_life",
  customTone: "",
  maxRounds: 6,
};

const character = {
  name: "夜班調查員",
  background: "熟悉門市每一個角落與所有交班紀錄。",
  trait: "遇事冷靜",
  weakness: "太容易懷疑自己",
  courage: 2,
  insight: 1,
  bond: 0,
};

async function createLobby(api) {
  await api.createRoom();
  return api.confirmWorld(world);
}

test("建立房間會回傳六碼代碼與空白 roster", async () => {
  const api = new MockGameApi();
  const room = await api.createRoom();

  assert.match(room.roomCode, /^[A-HJ-NP-Z2-9]{6}$/);
  assert.equal(room.round, 1);
  assert.equal(room.players.length, 0);
  assert.equal(room.status, "DRAFT");
});

test("加入房間會保存玩家並增加 version", async () => {
  const api = new MockGameApi();
  const original = await createLobby(api);
  const room = await api.joinRoom({ nickname: "小明", role: "細心的企劃" });

  assert.equal(room.players.length, 1);
  assert.equal(room.players[0].name, "小明");
  assert.equal(room.version, original.version + 1);
});

test("忽略大小寫的重複暱稱會被拒絕", async () => {
  const api = new MockGameApi();
  await createLobby(api);
  await api.joinRoom({ nickname: "Ming", role: "企劃" });

  await assert.rejects(
    api.joinRoom({ nickname: "ming", role: "工程師" }),
    { code: "NICKNAME_TAKEN", status: 409 },
  );
});

test("房間最多允許五位玩家", async () => {
  const api = new MockGameApi();
  await createLobby(api);
  for (let index = 1; index <= 5; index += 1) {
    await api.joinRoom({ nickname: `玩家${index}`, role: "測試角色" });
  }

  await assert.rejects(
    api.joinRoom({ nickname: "第六位", role: "測試角色" }),
    { code: "ROOM_FULL", status: 409 },
  );
});

test("回傳 snapshot 不允許 UI 直接修改 adapter state", async () => {
  const api = new MockGameApi();
  const room = await api.createRoom();
  room.roomCode = "BROKEN";

  const reloaded = await api.loadRoom();
  assert.notEqual(reloaded.roomCode, "BROKEN");
});

test("只有確認世界後才能加入，三位玩家後房主可開始", async () => {
  const api = new MockGameApi();
  await api.createRoom();
  await assert.rejects(
    api.joinRoom({ nickname: "甲", role: "企劃" }),
    { code: "ROOM_NOT_JOINABLE" },
  );
  const lobby = await api.confirmWorld(world);
  assert.equal(lobby.status, "LOBBY");
  for (const [nickname, role] of [["甲", "企劃"], ["乙", "工程師"], ["丙", "總務"]]) {
    await api.joinRoom({ nickname, role });
    await api.updateCharacter({ ...character, name: `角色${nickname}` });
  }
  const started = await api.startGame();
  assert.equal(started.status, "COLLECTING_ACTIONS");
  assert.equal(started.initialPlayerCount, 3);
});

test("角色配點完成前不能開始遊戲", async () => {
  const api = new MockGameApi();
  await createLobby(api);
  for (const [nickname, role] of [["甲", "企劃"], ["乙", "工程師"], ["丙", "總務"]]) {
    await api.joinRoom({ nickname, role });
  }
  await assert.rejects(api.startGame(), { code: "CHARACTERS_INCOMPLETE" });
  const ready = await api.updateCharacter(character);
  assert.equal(ready.players[2].characterReady, true);
  assert.equal(ready.players[2].character.spark, 1);
});

test("Mock adapter 可完成星火與一回合結算", async () => {
  const api = new MockGameApi();
  await createLobby(api);
  for (const [nickname, role] of [["甲", "企劃"], ["乙", "工程師"], ["丙", "總務"]]) {
    await api.joinRoom({ nickname, role });
    await api.updateCharacter({ ...character, name: `角色${nickname}` });
  }
  await api.startGame();
  api.room.players.forEach((player, index) => {
    player.action = `行動 ${index + 1}`;
    player.actionApproach = ["courage", "insight", "bond"][index];
  });
  api.room.status = "AWAITING_HOST";

  const rolled = await api.rollRound();
  assert.equal(rolled.status, "AWAITING_SPARK");
  const decided = await api.decideSpark({ decision: "USE" });
  assert.equal(decided.diceResults[2].sparkDecision, "USE");
  const resolved = await api.resolveRound({ skipPendingSpark: true });

  assert.equal(resolved.round, 2);
  assert.equal(resolved.status, "COLLECTING_ACTIONS");
  assert.equal(resolved.progressPoints > 0, true);
  assert.equal(resolved.entries.at(-1).type, "narrator");
  assert.equal(resolved.players.every((player) => player.action === ""), true);
});

test("Mock adapter 可模擬房主立即結局與繼續尾聲", async () => {
  const api = new MockGameApi();
  await api.createRoom();
  api.room.status = "COMPLETION_AVAILABLE";
  api.room.progressPoints = 18;
  api.room.dangerPoints = 9;
  api.room.targetPoints = 18;
  assert.equal(typeof api.finishGame, "function", "MockGameApi.finishGame 尚未建立");

  const continued = await api.finishGame({ decision: "CONTINUE" });
  assert.equal(continued.status, "COLLECTING_ACTIONS");
  assert.equal(continued.successLocked, true);

  api.room.status = "COMPLETION_AVAILABLE";
  const finished = await api.finishGame({ decision: "FINISH_NOW" });
  assert.equal(finished.status, "COMPLETED");
  assert.equal(finished.endingResult, "FULL_SUCCESS");
  assert.equal(finished.entries.at(-1).type, "ending");
});

test("Mock adapter 開始遊戲後提供與 HTTP adapter 相同的目標點數", async () => {
  const api = new MockGameApi();
  await createLobby(api);
  for (const [nickname, role] of [["甲", "企劃"], ["乙", "工程師"], ["丙", "總務"]]) {
    await api.joinRoom({ nickname, role });
    await api.updateCharacter({ ...character, name: `角色${nickname}` });
  }

  const started = await api.startGame();

  assert.equal(started.initialPlayerCount, 3);
  assert.equal(started.maxRounds, 6);
  assert.equal(started.targetPoints, 30);
  assert.equal(started.progressPercent, 0);
  assert.equal(started.dangerPercent, 0);
});

test("Mock adapter 非最終回合達 100% 時進入房主結局選擇", async () => {
  const api = new MockGameApi();
  api.room.session = {
    principalType: "host",
    playerId: null,
    csrfToken: "mock-host-csrf",
    isHost: true,
    hostCsrfToken: "mock-host-csrf",
  };
  api.room.status = "RESOLVING";
  api.room.round = 2;
  api.room.maxRounds = 6;
  api.room.initialPlayerCount = 3;
  api.room.progressPoints = 29;
  api.room.dangerPoints = 0;
  api.room.diceResults = api.room.players.map((player, index) => ({
    playerId: player.id,
    round: 2,
    result: index === 0 ? "SUCCESS" : "FAILURE",
    progressDelta: index === 0 ? 2 : 0,
    dangerDelta: 0,
    sparkUsed: 0,
    sparkDecision: "DECLINE",
  }));

  const resolved = await api.resolveRound();

  assert.equal(resolved.round, 3);
  assert.equal(resolved.targetPoints, 30);
  assert.equal(resolved.progressPercent, 100);
  assert.equal(resolved.status, "COMPLETION_AVAILABLE");
  assert.equal(resolved.endingResult, null);
});

test("Mock adapter 最終回合自動完成並輸出部分成功與顯著代價", async () => {
  const api = new MockGameApi();
  api.room.session = {
    principalType: "host",
    playerId: null,
    csrfToken: "mock-host-csrf",
    isHost: true,
    hostCsrfToken: "mock-host-csrf",
  };
  api.room.status = "RESOLVING";
  api.room.round = 6;
  api.room.maxRounds = 6;
  api.room.initialPlayerCount = 3;
  api.room.progressPoints = 17;
  api.room.dangerPoints = 11;
  api.room.diceResults = api.room.players.map((player) => ({
    playerId: player.id,
    round: 6,
    result: "PARTIAL_SUCCESS",
    progressDelta: 1,
    dangerDelta: 1,
    sparkUsed: 0,
    sparkDecision: "DECLINE",
  }));

  const resolved = await api.resolveRound();

  assert.equal(resolved.status, "COMPLETED");
  assert.equal(resolved.round, 6, "最終回合完成後不得增加回合數");
  assert.equal(resolved.targetPoints, 30);
  assert.equal(resolved.progressPercent, 67);
  assert.equal(resolved.dangerPercent, 47);
  assert.equal(resolved.endingResult, "PARTIAL_SUCCESS");
  assert.equal(resolved.endingCost, "SIGNIFICANT");
  assert.equal(resolved.entries.at(-1).type, "ending");
});

test("MockGameApi 提供 deterministic 世界草稿且最多生成兩次", async () => {
  const api = new MockGameApi();
  await api.createRoom();

  assert.equal(typeof api.generateWorld, "function", "MockGameApi.generateWorld 尚未建立");
  const first = await api.generateWorld({
    keywords: ["夜班", "便利商店", "盤點"],
    tone: "mystery",
    customTone: null,
    supplementalRequest: "讓玩家先編輯。",
  });
  const second = await api.generateWorld({
    keywords: ["夜班", "便利商店", "盤點"],
    tone: "mystery",
    customTone: null,
    supplementalRequest: "讓玩家先編輯。",
  });

  assert.equal(first.status, "DRAFT");
  assert.equal(first.worldGenerationCount, 1);
  assert.equal(first.world.storyTitle, "夜班便利商店盤點");
  assert.equal(second.worldGenerationCount, 2);
  await assert.rejects(
    api.generateWorld({
      keywords: ["夜班", "便利商店", "盤點"],
      tone: "mystery",
      customTone: null,
      supplementalRequest: "讓玩家先編輯。",
    }),
    { code: "WORLD_GENERATION_LIMIT", status: 409 },
  );
});
