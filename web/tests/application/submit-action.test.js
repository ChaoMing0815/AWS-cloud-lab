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
  });

  assert.deepEqual(command, { text: "我先確認出口。" });
});
