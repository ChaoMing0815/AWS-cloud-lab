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

test("FetchGameApi mutation 送出 Idempotency-Key", async () => {
  let request;
  const api = new FetchGameApi({
    idempotencyKeyFactory: () => "fixed-idempotency-key",
    fetchImpl: async (url, options) => {
      request = { url, options };
      return jsonResponse({ id: "room-1", version: 1, round: 1, players: [] }, 201);
    },
  });

  await api.createRoom();

  assert.equal(request.options.headers["Idempotency-Key"], "fixed-idempotency-key");
});

test("Submit action 只傳文字並帶 player session 的 CSRF token", async () => {
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

  await api.submitAction({ text: "我先確認出口。" });
  const request = requests[1];
  const body = JSON.parse(request.options.body);

  assert.equal(request.url, "/api/v1/rooms/room-1/rounds/1/action");
  assert.equal(request.options.headers["X-CSRF-Token"], "csrf-123");
  assert.equal(request.options.headers["Idempotency-Key"], "action-idempotency-key");
  assert.deepEqual(body, { text: "我先確認出口。", room_version: 3 });
  assert.equal("player_id" in body, false);
});
