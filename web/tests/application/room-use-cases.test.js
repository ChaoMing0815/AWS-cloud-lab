import test from "node:test";
import assert from "node:assert/strict";

import { CreateRoom } from "../../src/application/use-cases/create-room.js";
import { JoinRoom } from "../../src/application/use-cases/join-room.js";

test("CreateRoom 只透過 GameApi port 建立房間", async () => {
  let calls = 0;
  const expected = { id: "room-1" };
  const gameApi = {
    async createRoom() {
      calls += 1;
      return expected;
    },
  };

  assert.equal(await new CreateRoom(gameApi).execute(), expected);
  assert.equal(calls, 1);
});

test("JoinRoom 先正規化輸入再呼叫 GameApi port", async () => {
  let command;
  const gameApi = {
    async joinRoom(received) {
      command = received;
      return { players: [received] };
    },
  };

  const room = await new JoinRoom(gameApi).execute({
    nickname: "  小明 ",
    role: "  謹慎的工程師 ",
  });

  assert.deepEqual(command, { nickname: "小明", role: "謹慎的工程師" });
  assert.equal(room.players.length, 1);
});
