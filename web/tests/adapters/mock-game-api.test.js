import test from "node:test";
import assert from "node:assert/strict";

import { MockGameApi } from "../../src/adapters/api/mock-game-api.js";

test("建立房間會回傳六碼代碼與空白 roster", async () => {
  const api = new MockGameApi();
  const room = await api.createRoom();

  assert.match(room.roomCode, /^[A-HJ-NP-Z2-9]{6}$/);
  assert.equal(room.round, 1);
  assert.equal(room.players.length, 0);
});

test("加入房間會保存玩家並增加 version", async () => {
  const api = new MockGameApi();
  const original = await api.createRoom();
  const room = await api.joinRoom({ nickname: "小明", role: "細心的企劃" });

  assert.equal(room.players.length, 1);
  assert.equal(room.players[0].name, "小明");
  assert.equal(room.version, original.version + 1);
});

test("忽略大小寫的重複暱稱會被拒絕", async () => {
  const api = new MockGameApi();
  await api.createRoom();
  await api.joinRoom({ nickname: "Ming", role: "企劃" });

  await assert.rejects(
    api.joinRoom({ nickname: "ming", role: "工程師" }),
    { code: "NICKNAME_TAKEN", status: 409 },
  );
});

test("房間最多允許五位玩家", async () => {
  const api = new MockGameApi();
  await api.createRoom();
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
