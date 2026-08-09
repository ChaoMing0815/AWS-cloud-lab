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

test("GamePage 取得正式遊戲狀態後同步 canonical deep route", async () => {
  const routes = [];
  const page = new GamePage({
    navigate(route) {
      routes.push(route);
    },
  });
  page.setBusy = () => {};
  page.showFeedback = () => {};
  page.render = () => {};

  await page.run(async () => ({
    roomCode: "ABCD23",
    status: "COLLECTING_ACTIONS",
  }));

  assert.deepEqual(routes, ["/room/ABCD23/play"]);
});

test("GamePage 依房間階段同步 setup、lobby 與 ending route", async () => {
  const routes = [];
  const page = new GamePage({ navigate: (route) => routes.push(route) });
  page.setBusy = () => {};
  page.showFeedback = () => {};
  page.render = () => {};

  await page.run(async () => ({ roomCode: "ABCD23", status: "DRAFT" }));
  await page.run(async () => ({ roomCode: "ABCD23", status: "LOBBY" }));
  await page.run(async () => ({ roomCode: "ABCD23", status: "COMPLETED" }));

  assert.deepEqual(routes, [
    "/host/setup",
    "/room/ABCD23/lobby",
    "/room/ABCD23/ending",
  ]);
});
