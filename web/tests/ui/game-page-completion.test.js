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

test("GamePage 正式永久刪除確認後處理成功／失敗，Mock 分支維持建立新房間", async () => {
  const confirmations = [];
  const routes = [];
  let deleteCalls = 0;
  let createCalls = 0;
  const originalWindow = globalThis.window;
  globalThis.window = {
    confirm(message) {
      confirmations.push(message);
      return true;
    },
  };
  try {
    const page = new GamePage({
      apiMode: "http",
      deleteRoom: { async execute() { deleteCalls += 1; } },
      navigate: (route) => routes.push(route),
    });
    page.room = { status: "COMPLETED", session: { isHost: true } };
    page.run = async (operation) => {
      await operation();
      return true;
    };
    let stopCalls = 0;
    page.stopPolling = () => { stopCalls += 1; };

    assert.equal(typeof page.handleDeleteRoom, "function", "GamePage.handleDeleteRoom 尚未建立");
    await page.handleDeleteRoom();

    assert.equal(deleteCalls, 1);
    assert.equal(stopCalls, 1);
    assert.deepEqual(routes, ["/"]);
    assert.match(confirmations[0], /永久刪除/);
    assert.match(confirmations[0], /房主/);
    assert.match(confirmations[0], /所有資料/);
    const endingRoom = { status: "COMPLETED", session: { isHost: true } };
    const failedPage = new GamePage({
      apiMode: "http",
      deleteRoom: { async execute() { throw new Error("刪除失敗"); } },
      navigate: (route) => routes.push(route),
    });
    failedPage.room = endingRoom;
    failedPage.run = async () => false;
    let failedStopCalls = 0;
    failedPage.stopPolling = () => { failedStopCalls += 1; };
    await failedPage.handleDeleteRoom();
    assert.equal(failedPage.room, endingRoom, "失敗時必須保留結局畫面資料");
    assert.equal(failedStopCalls, 0);
    assert.deepEqual(routes, ["/"]);

    const mockPage = new GamePage({
      apiMode: "mock",
      createRoom: { async execute() { createCalls += 1; return { status: "DRAFT" }; } },
    });
    mockPage.run = async (operation) => operation();
    await mockPage.handleResetRoom();
    assert.equal(createCalls, 1, "Mock reset 應維持建立新房間，而非永久刪除");

    const originalDocument = globalThis.document;
    const nodes = new Map();
    globalThis.document = {
      getElementById(id) {
        if (!nodes.has(id)) nodes.set(id, {
          hidden: true, disabled: true, textContent: "", value: "", dataset: {},
        });
        return nodes.get(id);
      },
    };
    const completedHostView = {
      isHost: true,
      status: "COMPLETED",
      canEditWorld: false,
      canJoin: false,
      canStart: false,
      canEditCharacter: false,
      canRoll: false,
      canDecideSpark: false,
      canResolve: false,
      canRetryResolution: false,
      canUseFallback: false,
      canFinishNow: false,
      canContinue: false,
      currentDiceResult: null,
      players: [],
      readyTotal: 0,
    };
    try {
      page.renderHostControls(completedHostView);
      assert.equal(nodes.get("deleteRoomControls").hidden, false);
      assert.equal(nodes.get("deleteRoomButton").disabled, false);
      mockPage.renderHostControls(completedHostView);
      assert.equal(nodes.get("deleteRoomControls").hidden, true);
      assert.equal(nodes.get("deleteRoomButton").disabled, true);
    } finally {
      globalThis.document = originalDocument;
    }
  } finally {
    globalThis.window = originalWindow;
  }
});
