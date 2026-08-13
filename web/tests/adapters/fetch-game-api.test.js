import test from "node:test";
import assert from "node:assert/strict";

import { FetchGameApi } from "../../src/adapters/api/fetch-game-api.js";

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

test("FetchGameApi 以同源 cookie 載入目前房間", async () => {
  let request;
  const fetchImpl = async (url, options) => {
    request = { url, options };
    return jsonResponse({ id: "room-1", version: 1, round: 1 });
  };
  const api = new FetchGameApi({ basePath: "/api/v1", fetchImpl });

  await api.loadRoom();

  assert.equal(request.url, "/api/v1/rooms/current");
  assert.equal(request.options.credentials, "include");
});

test("FetchGameApi 以同源 cookie 讀取安全 session 摘要", async () => {
  let request;
  const summary = {
    authenticated: true,
    principalType: "player",
    isHost: false,
    room: { id: "room-1", roomCode: "ABCD23", status: "LOBBY" },
    continueRoute: "/room/ABCD23/lobby",
  };
  const api = new FetchGameApi({
    fetchImpl: async (url, options) => {
      request = { url, options };
      return jsonResponse(summary);
    },
  });

  const observed = await api.loadCurrentSession();

  assert.equal(request.url, "/api/v1/session/current");
  assert.equal(request.options.credentials, "include");
  assert.deepEqual(observed, summary);
});

test("FetchGameApi 加入房間時傳送已知 room version", async () => {
  const requests = [];
  const responses = [
    { id: "room-1", version: 4, round: 1 },
    { id: "room-1", version: 5, round: 1, players: [{ name: "小明" }] },
  ];
  const fetchImpl = async (url, options) => {
    requests.push({ url, options });
    return jsonResponse(responses.shift());
  };
  const api = new FetchGameApi({ fetchImpl });
  await api.loadRoom();

  const room = await api.joinRoom({ nickname: "小明", role: "企劃" });
  const body = JSON.parse(requests[1].options.body);

  assert.equal(requests[1].url, "/api/v1/rooms/room-1/players");
  assert.equal(body.room_version, 4);
  assert.equal(room.version, 5);
});

test("FetchGameApi 將 structured API error 轉為 ApiError", async () => {
  const api = new FetchGameApi({
    fetchImpl: async () => jsonResponse(
      { error: { code: "VERSION_CONFLICT", message: "請重新載入。" } },
      409,
    ),
  });

  await assert.rejects(api.loadRoom(), {
    code: "VERSION_CONFLICT",
    status: 409,
    message: "請重新載入。",
  });
});

test("FetchGameApi 將 FastAPI 422 detail 轉為可標示欄位的錯誤", async () => {
  const api = new FetchGameApi({
    fetchImpl: async () => jsonResponse(
      {
        detail: [{
          type: "string_too_short",
          loc: ["body", "premise"],
          msg: "String should have at least 50 characters",
          ctx: { min_length: 50 },
        }],
      },
      422,
    ),
  });

  await assert.rejects(api.loadRoom(), (error) => {
    assert.equal(error.code, "REQUEST_VALIDATION_FAILED");
    assert.equal(error.status, 422);
    assert.equal(error.message, "請檢查標示的欄位。");
    assert.deepEqual(error.fieldErrors, { premise: "至少需要 50 個字元。" });
    return true;
  });
});

test("FetchGameApi 建立房間時送出房主暱稱與 Idempotency-Key", async () => {
  let request;
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "fixed-idempotency-key",
    fetchImpl: async (url, options) => {
      request = { url, options };
      return jsonResponse({ id: "room-1", version: 1, round: 1, players: [] }, 201);
    },
  });

  await api.createRoom({ nickname: "昭銘" });

  assert.equal(request.options.headers["Idempotency-Key"], "fixed-idempotency-key");
  assert.equal(request.options.body, JSON.stringify({ nickname: "昭銘" }));
});

test("FetchGameApi 不需目前房間即可用房號加入", async () => {
  let request;
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "join-by-code-key",
    fetchImpl: async (url, options) => {
      request = { url, options };
      return jsonResponse({ roomCode: "ABCD23", version: 4, players: [] }, 201);
    },
  });

  const room = await api.joinRoomByCode({ roomCode: "ABCD23", nickname: "小明" });

  assert.equal(request.url, "/api/v1/rooms:join");
  assert.equal(request.options.headers["Idempotency-Key"], "join-by-code-key");
  assert.deepEqual(JSON.parse(request.options.body), {
    room_code: "ABCD23",
    nickname: "小明",
  });
  assert.equal(room.roomCode, "ABCD23");
});

test("Submit action 傳送文字與行動方式並帶 player session 的 CSRF token", async () => {
  const requests = [];
  const room = {
    id: "room-1",
    version: 3,
    round: 1,
    players: [{ id: "player-1", name: "小明" }],
    session: { principalType: "player", playerId: "player-1", csrfToken: "csrf-123" },
  };
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "action-idempotency-key",
    fetchImpl: async (url, options) => {
      requests.push({ url, options });
      return jsonResponse(room);
    },
  });
  await api.loadRoom();

  await api.submitAction({ text: "我先確認出口。", approach: "insight" });
  const request = requests[1];
  const body = JSON.parse(request.options.body);

  assert.equal(request.url, "/api/v1/rooms/room-1/rounds/1/action");
  assert.equal(request.options.headers["X-CSRF-Token"], "csrf-123");
  assert.equal(request.options.headers["Idempotency-Key"], "action-idempotency-key");
  assert.deepEqual(body, { text: "我先確認出口。", approach: "insight", room_version: 3 });
  assert.equal("player_id" in body, false);
});

test("房主擲骰使用 host CSRF token 與目前回合版本", async () => {
  const requests = [];
  const room = {
    id: "room-1",
    version: 9,
    round: 2,
    status: "AWAITING_HOST",
    players: [],
    session: { isHost: true, hostCsrfToken: "host-roll-csrf" },
  };
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "roll-key",
    fetchImpl: async (url, options) => {
      requests.push({ url, options });
      return jsonResponse(room);
    },
  });
  await api.loadRoom();
  await api.rollRound();

  const request = requests[1];
  assert.equal(request.url, "/api/v1/rooms/room-1/rounds/2:roll");
  assert.equal(request.options.headers["X-CSRF-Token"], "host-roll-csrf");
  assert.equal(request.options.headers["Idempotency-Key"], "roll-key");
  assert.deepEqual(JSON.parse(request.options.body), { room_version: 9 });
});

test("星火決策與房主結算使用各自 CSRF 邊界", async () => {
  const requests = [];
  const room = {
    id: "room-1",
    version: 12,
    round: 3,
    status: "AWAITING_SPARK",
    players: [],
    session: {
      principalType: "player",
      playerId: "player-1",
      csrfToken: "player-spark-csrf",
      isHost: true,
      hostCsrfToken: "host-resolve-csrf",
    },
  };
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "round-mutation-key",
    fetchImpl: async (url, options) => {
      requests.push({ url, options });
      return jsonResponse(room);
    },
  });
  await api.loadRoom();
  await api.decideSpark({ decision: "USE" });
  await api.resolveRound({ skipPendingSpark: true });

  const sparkRequest = requests[1];
  const resolveRequest = requests[2];
  assert.equal(sparkRequest.url, "/api/v1/rooms/room-1/rounds/3/spark");
  assert.equal(sparkRequest.options.headers["X-CSRF-Token"], "player-spark-csrf");
  assert.deepEqual(JSON.parse(sparkRequest.options.body), {
    decision: "USE",
    room_version: 12,
  });
  assert.equal(resolveRequest.url, "/api/v1/rooms/room-1/rounds/3:resolve");
  assert.equal(resolveRequest.options.headers["X-CSRF-Token"], "host-resolve-csrf");
  assert.deepEqual(JSON.parse(resolveRequest.options.body), {
    skip_pending_spark: true,
    room_version: 12,
  });
});

test("房主 fallback 使用鎖定回合版本與 host CSRF", async () => {
  const requests = [];
  const room = {
    id: "room-fallback",
    version: 15,
    round: 4,
    status: "RESOLUTION_FAILED",
    players: [],
    session: { isHost: true, hostCsrfToken: "host-fallback-csrf" },
  };
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "fallback-key",
    fetchImpl: async (url, options) => {
      requests.push({ url, options });
      return jsonResponse(room);
    },
  });
  await api.loadRoom();

  await api.fallbackRound();

  const request = requests[1];
  assert.equal(request.url, "/api/v1/rooms/room-fallback/rounds/4:fallback");
  assert.equal(request.options.headers["X-CSRF-Token"], "host-fallback-csrf");
  assert.equal(request.options.headers["Idempotency-Key"], "fallback-key");
  assert.deepEqual(JSON.parse(request.options.body), { room_version: 15 });
});

test("房主確認世界與開始遊戲使用 host CSRF token", async () => {
  const requests = [];
  const room = {
    id: "room-1",
    version: 1,
    round: 1,
    status: "DRAFT",
    players: [],
    session: { isHost: true, hostCsrfToken: "host-csrf-123" },
  };
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "host-mutation-key",
    fetchImpl: async (url, options) => {
      requests.push({ url, options });
      return jsonResponse({ ...room, version: room.version + requests.length - 1 });
    },
  });
  await api.loadRoom();
  await api.confirmWorld({
    storyTitle: "測試故事",
    premise: "這是一段符合長度規範的測試世界背景，用來驗證房主請求資料能正確送到後端處理。",
    objective: "完成共同測試目標。",
    openingScene: "所有玩家在測試場景集合並準備開始。",
    coreObstacle: "必須通過所有驗證關卡。",
    tone: "light_comedy",
    customTone: "",
    maxRounds: 4,
  });
  await api.startGame();

  assert.equal(requests[1].url, "/api/v1/rooms/room-1/world");
  assert.equal(requests[2].url, "/api/v1/rooms/room-1:start");
  assert.equal(requests[1].options.headers["X-CSRF-Token"], "host-csrf-123");
  assert.equal(requests[2].options.headers["X-CSRF-Token"], "host-csrf-123");
  assert.equal(requests[1].options.headers["Idempotency-Key"], "host-mutation-key");
});

test("角色更新使用 player CSRF 且不接受 player ID", async () => {
  const requests = [];
  const room = {
    id: "room-1",
    version: 7,
    round: 1,
    players: [],
    session: { principalType: "player", playerId: "player-1", csrfToken: "player-csrf" },
  };
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "character-key",
    fetchImpl: async (url, options) => {
      requests.push({ url, options });
      return jsonResponse(room);
    },
  });
  await api.loadRoom();
  await api.updateCharacter({
    name: "調查員",
    background: "熟悉所有交班紀錄。",
    trait: "冷靜",
    weakness: "多疑",
    courage: 2,
    insight: 1,
    bond: 0,
  });
  const request = requests[1];
  const body = JSON.parse(request.options.body);
  assert.equal(request.url, "/api/v1/rooms/room-1/character");
  assert.equal(request.options.headers["X-CSRF-Token"], "player-csrf");
  assert.equal(request.options.headers["Idempotency-Key"], "character-key");
  assert.equal(body.room_version, 7);
  assert.equal("player_id" in body, false);
});

test("房主結局選擇使用 finish endpoint 與 host CSRF", async () => {
  const requests = [];
  const room = {
    id: "room-1",
    version: 15,
    round: 3,
    status: "COMPLETION_AVAILABLE",
    players: [],
    session: { isHost: true, hostCsrfToken: "host-finish-csrf" },
  };
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "finish-mutation-key",
    fetchImpl: async (url, options) => {
      requests.push({ url, options });
      return jsonResponse(room);
    },
  });
  await api.loadRoom();
  assert.equal(typeof api.finishGame, "function", "FetchGameApi.finishGame 尚未建立");

  await api.finishGame({ decision: "CONTINUE" });

  const request = requests[1];
  assert.equal(request.url, "/api/v1/rooms/room-1:finish");
  assert.equal(request.options.headers["X-CSRF-Token"], "host-finish-csrf");
  assert.equal(request.options.headers["Idempotency-Key"], "finish-mutation-key");
  assert.deepEqual(JSON.parse(request.options.body), {
    decision: "CONTINUE",
    room_version: 15,
  });
});

test("房主永久刪除房間時送出 version、host CSRF 與 Idempotency-Key", async () => {
  const requests = [];
  const room = {
    id: "room-delete",
    version: 16,
    status: "COMPLETED",
    session: { isHost: true, hostCsrfToken: "host-delete-csrf" },
  };
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "delete-room-key",
    fetchImpl: async (url, options) => {
      requests.push({ url, options });
      if (options.method === "DELETE") return new Response(null, { status: 204 });
      return jsonResponse(room);
    },
  });
  await api.loadRoom();

  assert.equal(typeof api.deleteRoom, "function", "FetchGameApi.deleteRoom 尚未建立");
  await api.deleteRoom();

  const request = requests[1];
  assert.equal(request.url, "/api/v1/rooms/room-delete");
  assert.equal(request.options.method, "DELETE");
  assert.equal(request.options.credentials, "include");
  assert.equal(request.options.headers["X-CSRF-Token"], "host-delete-csrf");
  assert.equal(request.options.headers["Idempotency-Key"], "delete-room-key");
  assert.deepEqual(JSON.parse(request.options.body), { room_version: 16 });
  assert.equal(api.room, null, "成功刪除後不應保留過期房間狀態");
});

test("FetchGameApi 生成世界草稿時帶 canonical version、host CSRF 與 Idempotency-Key", async () => {
  const requests = [];
  const draft = {
    id: "room-world",
    version: 2,
    status: "DRAFT",
    worldGenerationCount: 1,
    session: { isHost: true, hostCsrfToken: "host-world-csrf" },
  };
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "world-generation-key",
    fetchImpl: async (url, options) => {
      requests.push({ url, options });
      return jsonResponse(draft);
    },
  });
  api.room = {
    id: "room-world",
    version: 1,
    status: "DRAFT",
    session: { isHost: true, hostCsrfToken: "host-world-csrf" },
  };

  assert.equal(typeof api.generateWorld, "function", "FetchGameApi.generateWorld 尚未建立");
  const room = await api.generateWorld({
    keywords: ["夜班", "便利商店", "盤點"],
    tone: "mystery",
    customTone: null,
    supplementalRequest: "讓玩家先編輯。",
  });

  const request = requests[0];
  assert.equal(request.url, "/api/v1/rooms/room-world/world:generate");
  assert.equal(request.options.method, "POST");
  assert.equal(request.options.headers["X-CSRF-Token"], "host-world-csrf");
  assert.equal(request.options.headers["Idempotency-Key"], "world-generation-key");
  assert.deepEqual(JSON.parse(request.options.body), {
    keywords: ["夜班", "便利商店", "盤點"],
    tone: "mystery",
    custom_tone: null,
    supplemental_request: "讓玩家先編輯。",
    room_version: 1,
  });
  assert.equal(room.worldGenerationCount, 1);
});
