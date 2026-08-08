import test from "node:test";
import assert from "node:assert/strict";

import { SubmitAction } from "../../src/application/use-cases/submit-action.js";

test("SubmitAction 不接受前端指定 player ID", async () => {
  let command;
  const gameApi = {
    async submitAction(received) {
      command = received;
      return { version: 2 };
    },
  };

  await new SubmitAction(gameApi).execute({
    playerId: "attacker-selected-player",
    text: "  我先確認出口。  ",
    approach: "insight",
  });

  assert.deepEqual(command, { text: "我先確認出口。", approach: "insight" });
});

test("SubmitAction 拒絕未知的行動方式", async () => {
  assert.throws(
    () => new SubmitAction({ submitAction() {} }).execute({ text: "前進", approach: "magic" }),
    { code: "INVALID_APPROACH" },
  );
});
