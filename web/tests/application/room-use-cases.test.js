import test from "node:test";
import assert from "node:assert/strict";

import { CreateRoom } from "../../src/application/use-cases/create-room.js";
import { ConfirmWorld } from "../../src/application/use-cases/confirm-world.js";
import { JoinRoom } from "../../src/application/use-cases/join-room.js";
import { StartGame } from "../../src/application/use-cases/start-game.js";
import { UpdateCharacter } from "../../src/application/use-cases/update-character.js";
import { DecideSpark } from "../../src/application/use-cases/decide-spark.js";
import { ResolveRound } from "../../src/application/use-cases/resolve-round.js";

let FinishGame;
try {
  ({ FinishGame } = await import("../../src/application/use-cases/finish-game.js"));
} catch {
  FinishGame = undefined;
}

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

test("ConfirmWorld 正規化文字並驗證回合上限", async () => {
  let command;
  const gameApi = {
    async confirmWorld(received) {
      command = received;
      return { status: "LOBBY" };
    },
  };
  const useCase = new ConfirmWorld(gameApi);
  await useCase.execute({
    storyTitle: "  測試故事 ",
    premise: "  足夠長的背景 ",
    objective: "  共同目標 ",
    openingScene: "  初始場景 ",
    coreObstacle: "  核心阻礙 ",
    tone: "light_comedy",
    customTone: "  ",
    maxRounds: 6,
  });
  assert.equal(command.storyTitle, "測試故事");
  assert.equal(command.customTone, "");
  await assert.rejects(
    useCase.execute({ tone: "light_comedy", maxRounds: 5 }),
    { code: "INVALID_ROUND_LIMIT" },
  );
});

test("StartGame 只透過 GameApi port 開始遊戲", async () => {
  let calls = 0;
  const gameApi = {
    async startGame() {
      calls += 1;
      return { status: "COLLECTING_ACTIONS" };
    },
  };
  const room = await new StartGame(gameApi).execute();
  assert.equal(room.status, "COLLECTING_ACTIONS");
  assert.equal(calls, 1);
});

test("UpdateCharacter 正規化欄位並只接受合法三點配點", async () => {
  let command;
  const gameApi = {
    async updateCharacter(received) {
      command = received;
      return { characterReady: true };
    },
  };
  const useCase = new UpdateCharacter(gameApi);
  await useCase.execute({
    name: "  調查員 ",
    background: "  熟悉所有交班紀錄。 ",
    trait: "  冷靜 ",
    weakness: "  多疑 ",
    courage: "2",
    insight: "1",
    bond: "0",
  });
  assert.equal(command.name, "調查員");
  assert.deepEqual([command.courage, command.insight, command.bond], [2, 1, 0]);
  await assert.rejects(
    useCase.execute({
      name: "角色",
      background: "背景",
      trait: "特質",
      weakness: "弱點",
      courage: 2,
      insight: 2,
      bond: 0,
    }),
    { code: "INVALID_ATTRIBUTE_TOTAL" },
  );
});

test("DecideSpark 只接受 USE 或 DECLINE", async () => {
  let command;
  const gameApi = {
    async decideSpark(received) {
      command = received;
      return { status: "RESOLVING" };
    },
  };
  const useCase = new DecideSpark(gameApi);
  await useCase.execute({ decision: "USE" });
  assert.deepEqual(command, { decision: "USE" });
  assert.throws(
    () => useCase.execute({ decision: "TRANSFER" }),
    { code: "INVALID_SPARK_DECISION" },
  );
});

test("ResolveRound 明確傳送是否略過等待者", async () => {
  let command;
  const gameApi = {
    async resolveRound(received) {
      command = received;
      return { round: 2 };
    },
  };
  const room = await new ResolveRound(gameApi).execute({ skipPendingSpark: true });
  assert.deepEqual(command, { skipPendingSpark: true });
  assert.equal(room.round, 2);
});

test("FinishGame 只接受 FINISH_NOW 或 CONTINUE", async () => {
  assert.equal(typeof FinishGame, "function", "FinishGame use case 尚未建立");
  let command;
  const gameApi = {
    async finishGame(received) {
      command = received;
      return { status: "COMPLETED" };
    },
  };
  const useCase = new FinishGame(gameApi);

  const room = await useCase.execute({ decision: "FINISH_NOW" });

  assert.deepEqual(command, { decision: "FINISH_NOW" });
  assert.equal(room.status, "COMPLETED");
  assert.throws(
    () => useCase.execute({ decision: "REWRITE_ENDING" }),
    { code: "INVALID_COMPLETION_DECISION" },
  );
});
