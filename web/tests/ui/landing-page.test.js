import test from "node:test";
import assert from "node:assert/strict";

let LandingPage;
try {
  ({ LandingPage } = await import("../../src/ui/pages/landing-page.js"));
} catch {
  LandingPage = undefined;
}

function fakeDocument(nickname = "昭銘") {
  const elements = {
    createGameForm: {},
    hostNickname: { value: nickname },
    createGameButton: { disabled: false },
    createGameError: { hidden: true, textContent: "" },
    joinRoomCode: { value: " abcd23 " },
    joinNickname: { value: " 小明 " },
    joinGameButton: { disabled: false },
    joinGameError: { hidden: true, textContent: "" },
    continueGamePanel: { hidden: true },
    continueGameButton: { disabled: false },
    currentGameSummary: { textContent: "" },
    sessionNotice: { hidden: true, textContent: "" },
  };
  return {
    elements,
    getElementById(id) {
      return elements[id];
    },
  };
}

test("LandingPage 建房成功後只導航一次至世界設定", async () => {
  assert.equal(typeof LandingPage, "function", "LandingPage controller 尚未建立");
  const documentRef = fakeDocument("  昭銘  ");
  const commands = [];
  const routes = [];
  const page = new LandingPage({
    createRoom: {
      async execute(command) {
        commands.push(command);
        return { id: "room-1" };
      },
    },
    documentRef,
    navigate: (route) => routes.push(route),
  });

  await page.handleCreate({ preventDefault() {} });

  assert.deepEqual(commands, [{ nickname: "  昭銘  " }]);
  assert.deepEqual(routes, ["/host/setup"]);
  assert.equal(documentRef.elements.createGameButton.disabled, false);
  assert.equal(documentRef.elements.createGameError.hidden, true);
});

test("LandingPage 有有效 session 時顯示繼續入口並依 canonical route 導航", async () => {
  const documentRef = fakeDocument();
  const routes = [];
  const page = new LandingPage({
    createRoom: { async execute() {} },
    joinRoomByCode: { async execute() {} },
    loadCurrentSession: {
      async execute() {
        return {
          authenticated: true,
          room: { roomCode: "ABCD23", status: "LOBBY" },
          continueRoute: "/room/ABCD23/lobby",
        };
      },
    },
    documentRef,
    navigate: (route) => routes.push(route),
  });

  await page.restoreCurrentSession();
  await page.handleContinue();

  assert.equal(documentRef.elements.continueGamePanel.hidden, false);
  assert.match(documentRef.elements.currentGameSummary.textContent, /ABCD23/);
  assert.deepEqual(routes, ["/room/ABCD23/lobby"]);
});

test("LandingPage 匿名時不顯示繼續入口", async () => {
  const documentRef = fakeDocument();
  const page = new LandingPage({
    createRoom: { async execute() {} },
    joinRoomByCode: { async execute() {} },
    loadCurrentSession: {
      async execute() {
        return { authenticated: false, continueRoute: null };
      },
    },
    documentRef,
    navigate() {},
  });

  await page.restoreCurrentSession();

  assert.equal(documentRef.elements.continueGamePanel.hidden, true);
  assert.equal(documentRef.elements.sessionNotice.hidden, true);
});

test("LandingPage 過期 session 留在首頁並顯示原因", async () => {
  const documentRef = fakeDocument();
  const page = new LandingPage({
    createRoom: { async execute() {} },
    joinRoomByCode: { async execute() {} },
    loadCurrentSession: {
      async execute() {
        const error = new Error("目前的遊戲工作階段已失效。");
        error.code = "SESSION_NOT_FOUND";
        throw error;
      },
    },
    documentRef,
    navigate() {},
  });

  await page.restoreCurrentSession();

  assert.equal(documentRef.elements.continueGamePanel.hidden, true);
  assert.equal(documentRef.elements.sessionNotice.hidden, false);
  assert.equal(documentRef.elements.sessionNotice.textContent, "目前的遊戲工作階段已失效。");
});

test("LandingPage 加入成功後依回傳房號前往 Lobby", async () => {
  assert.equal(typeof LandingPage, "function", "LandingPage controller 尚未建立");
  const documentRef = fakeDocument();
  const commands = [];
  const routes = [];
  const page = new LandingPage({
    createRoom: { async execute() {} },
    joinRoomByCode: {
      async execute(command) {
        commands.push(command);
        return { roomCode: "ABCD23" };
      },
    },
    documentRef,
    navigate: (route) => routes.push(route),
  });

  await page.handleJoin({ preventDefault() {} });

  assert.deepEqual(commands, [{ roomCode: " abcd23 ", nickname: " 小明 " }]);
  assert.deepEqual(routes, ["/room/ABCD23/lobby"]);
  assert.equal(documentRef.elements.joinGameButton.disabled, false);
  assert.equal(documentRef.elements.joinGameError.hidden, true);
});

test("LandingPage 加入失敗時留在首頁並顯示錯誤", async () => {
  const documentRef = fakeDocument();
  const routes = [];
  const page = new LandingPage({
    createRoom: { async execute() {} },
    joinRoomByCode: {
      async execute() {
        throw new Error("找不到此房間。");
      },
    },
    documentRef,
    navigate: (route) => routes.push(route),
  });

  await page.handleJoin({ preventDefault() {} });

  assert.deepEqual(routes, []);
  assert.equal(documentRef.elements.joinGameError.hidden, false);
  assert.equal(documentRef.elements.joinGameError.textContent, "找不到此房間。");
});

test("LandingPage 將世界尚未開放的 409 顯示為明確玩家提示", async () => {
  const documentRef = fakeDocument();
  const routes = [];
  const page = new LandingPage({
    createRoom: { async execute() {} },
    joinRoomByCode: {
      async execute() {
        const error = new Error("只有等待中的房間可以加入玩家。");
        error.code = "ROOM_NOT_JOINABLE";
        error.status = 409;
        throw error;
      },
    },
    documentRef,
    navigate: (route) => routes.push(route),
  });

  await page.handleJoin({ preventDefault() {} });

  assert.deepEqual(routes, []);
  assert.equal(documentRef.elements.joinGameError.hidden, false);
  assert.equal(
    documentRef.elements.joinGameError.textContent,
    "房主尚未開放世界，請稍後再試。",
  );
  assert.equal(documentRef.elements.joinGameButton.disabled, false);
});

test("LandingPage 建房失敗時留在首頁並顯示錯誤", async () => {
  assert.equal(typeof LandingPage, "function", "LandingPage controller 尚未建立");
  const documentRef = fakeDocument("   ");
  const routes = [];
  const page = new LandingPage({
    createRoom: {
      async execute() {
        throw new Error("請輸入暱稱。");
      },
    },
    documentRef,
    navigate: (route) => routes.push(route),
  });

  await page.handleCreate({ preventDefault() {} });

  assert.deepEqual(routes, []);
  assert.equal(documentRef.elements.createGameError.hidden, false);
  assert.equal(documentRef.elements.createGameError.textContent, "請輸入暱稱。");
  assert.equal(documentRef.elements.createGameButton.disabled, false);
});
