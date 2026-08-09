import test from "node:test";
import assert from "node:assert/strict";

import { GamePage } from "../../src/ui/pages/game-page.js";


test("GamePage 將房主結局選擇交給 FinishGame use case", async () => {
  let command;
  const page = new GamePage({
    finishGame: {
      async execute(received) {
        command = received;
        return { status: "COMPLETED" };
      },
    },
  });
  page.run = (operation) => operation();

  assert.equal(typeof page.handleFinish, "function", "GamePage.handleFinish 尚未建立");
  await page.handleFinish("FINISH_NOW");

  assert.deepEqual(command, { decision: "FINISH_NOW" });
});
