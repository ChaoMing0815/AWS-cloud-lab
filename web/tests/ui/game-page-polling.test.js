import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import { ApiError } from "../../src/adapters/api/api-error.js";
import { GamePage } from "../../src/ui/pages/game-page.js";

function createScheduler() {
  const tasks = [];
  const cancelled = [];
  return {
    tasks,
    cancelled,
    schedule(callback, delay) {
      const id = tasks.length + 1;
      tasks.push({ id, callback, delay });
      return id;
    },
    cancel(id) {
      cancelled.push(id);
    },
  };
}

function installPollingStatusDocument() {
  const pollingStatus = {
    dataset: {},
    hidden: true,
    textContent: "",
  };
  const previousDocument = globalThis.document;
  globalThis.document = {
    getElementById(id) {
      if (id === "pollingStatus") return pollingStatus;
      return null;
    },
  };
  return {
    pollingStatus,
    restore() {
      globalThis.document = previousDocument;
    },
  };
}

test("GamePage 每次 polling 完成後才排定下一次同步", async () => {
  const scheduler = createScheduler();
  let loadCount = 0;
  let renderCount = 0;
  const page = new GamePage({
    loadRoom: {
      async execute() {
        loadCount += 1;
        return { status: "COLLECTING_ACTIONS", version: loadCount };
      },
    },
    schedule: scheduler.schedule,
    cancelSchedule: scheduler.cancel,
    pollingIntervalMs: 3000,
  });
  page.room = { status: "COLLECTING_ACTIONS", version: 0 };
  page.render = () => { renderCount += 1; };

  assert.equal(typeof page.startPolling, "function", "GamePage.startPolling 尚未建立");
  page.startPolling();

  assert.equal(scheduler.tasks.length, 1);
  assert.equal(scheduler.tasks[0].delay, 3000);
  await scheduler.tasks[0].callback();

  assert.equal(loadCount, 1);
  assert.equal(renderCount, 1);
  assert.equal(page.room.version, 1);
  assert.equal(scheduler.tasks.length, 2, "同步完成後才排定下一次 polling");
});

test("GamePage 不允許重疊的 polling request", async () => {
  let release;
  let loadCount = 0;
  const pending = new Promise((resolve) => { release = resolve; });
  const page = new GamePage({
    loadRoom: {
      async execute() {
        loadCount += 1;
        await pending;
        return { status: "COLLECTING_ACTIONS" };
      },
    },
    schedule: () => 1,
    cancelSchedule: () => {},
  });
  page.room = { status: "COLLECTING_ACTIONS" };
  page.render = () => {};

  assert.equal(typeof page.pollOnce, "function", "GamePage.pollOnce 尚未建立");
  const first = page.pollOnce();
  const second = page.pollOnce();

  assert.equal(loadCount, 1);
  release();
  await Promise.all([first, second]);
  assert.equal(loadCount, 1);
});

test("GamePage 在結局完成後停止 polling", async () => {
  const scheduler = createScheduler();
  const page = new GamePage({
    loadRoom: { async execute() { return { status: "COMPLETED" }; } },
    schedule: scheduler.schedule,
    cancelSchedule: scheduler.cancel,
  });
  page.room = { status: "COMPLETED" };

  page.startPolling();

  assert.equal(scheduler.tasks.length, 0);
});

test("GamePage 停止時取消已排定的 polling", () => {
  const scheduler = createScheduler();
  const page = new GamePage({
    loadRoom: { async execute() { return { status: "COLLECTING_ACTIONS" }; } },
    schedule: scheduler.schedule,
    cancelSchedule: scheduler.cancel,
  });
  page.room = { status: "COLLECTING_ACTIONS" };

  page.startPolling();
  assert.equal(typeof page.stopPolling, "function", "GamePage.stopPolling 尚未建立");
  page.stopPolling();

  assert.deepEqual(scheduler.cancelled, [scheduler.tasks[0].id]);
});

test("GamePage 暫時離線時保留 canonical 畫面並以 3、5、10 秒 bounded backoff 重試", async () => {
  const scheduler = createScheduler();
  const statusDocument = installPollingStatusDocument();
  const failures = [
    new TypeError("Failed to fetch"),
    new ApiError("UPSTREAM_ERROR", "暫時失敗", 503),
    new ApiError("BAD_GATEWAY", "暫時失敗", 502),
    new TypeError("Network connection lost"),
  ];
  const canonicalRoom = { status: "COLLECTING_ACTIONS", version: 7 };
  let renderCount = 0;
  const page = new GamePage({
    loadRoom: {
      async execute() {
        throw failures.shift();
      },
    },
    schedule: scheduler.schedule,
    cancelSchedule: scheduler.cancel,
  });
  page.room = canonicalRoom;
  page.render = () => { renderCount += 1; };

  try {
    page.startPolling();
    for (let index = 0; index < 4; index += 1) {
      await assert.doesNotReject(
        scheduler.tasks[index].callback(),
        "暫時 polling 失敗應由 GamePage 處理，不可成為未捕捉錯誤",
      );
    }

    assert.deepEqual(
      scheduler.tasks.map(({ delay }) => delay),
      [3000, 3000, 5000, 10000, 10000],
    );
    assert.strictEqual(page.room, canonicalRoom, "離線期間必須保留最後 canonical state");
    assert.equal(renderCount, 0, "離線失敗不得用空白或錯誤 payload 覆寫畫面");
    assert.equal(statusDocument.pollingStatus.hidden, false);
    assert.equal(statusDocument.pollingStatus.dataset.kind, "offline");
    assert.equal(
      statusDocument.pollingStatus.textContent,
      "連線中斷，將在 10 秒後重試。",
    );
  } finally {
    statusDocument.restore();
  }
});

test("GamePage 重新連線後更新 canonical state 並恢復 3 秒 polling", async () => {
  const scheduler = createScheduler();
  const statusDocument = installPollingStatusDocument();
  const recoveredRoom = { status: "COLLECTING_ACTIONS", version: 8 };
  const responses = [new TypeError("Failed to fetch"), recoveredRoom];
  let renderCount = 0;
  const page = new GamePage({
    loadRoom: {
      async execute() {
        const response = responses.shift();
        if (response instanceof Error) throw response;
        return response;
      },
    },
    schedule: scheduler.schedule,
    cancelSchedule: scheduler.cancel,
  });
  page.room = { status: "COLLECTING_ACTIONS", version: 7 };
  page.render = () => { renderCount += 1; };
  page.syncRoute = () => {};

  try {
    page.startPolling();
    await assert.doesNotReject(scheduler.tasks[0].callback());
    await assert.doesNotReject(scheduler.tasks[1].callback());

    assert.strictEqual(page.room, recoveredRoom);
    assert.equal(renderCount, 1);
    assert.equal(scheduler.tasks[2].delay, 3000);
    assert.equal(statusDocument.pollingStatus.dataset.kind, "reconnected");
    assert.equal(statusDocument.pollingStatus.textContent, "已重新連線，資料已同步。");
  } finally {
    statusDocument.restore();
  }
});

test("GamePage 遇到 401 或 403 時停止 polling 並顯示 session 下一步", async () => {
  for (const status of [401, 403]) {
    const scheduler = createScheduler();
    const statusDocument = installPollingStatusDocument();
    const page = new GamePage({
      loadRoom: {
        async execute() {
          throw new ApiError("SESSION_INVALID", "session 已失效", status);
        },
      },
      schedule: scheduler.schedule,
      cancelSchedule: scheduler.cancel,
    });
    page.room = { status: "COLLECTING_ACTIONS", version: 7 };

    try {
      page.startPolling();
      await assert.doesNotReject(scheduler.tasks[0].callback());

      assert.equal(page.pollingStopped, true, `${status} 必須停止 polling`);
      assert.equal(scheduler.tasks.length, 1, `${status} 不得再排定 retry`);
      assert.equal(statusDocument.pollingStatus.dataset.kind, "session-expired");
      assert.equal(
        statusDocument.pollingStatus.textContent,
        "登入狀態已失效，請回首頁重新加入。",
      );
    } finally {
      statusDocument.restore();
    }
  }
});

test("GamePage 房間被刪除後停止 polling、清除舊房間並只導回首頁一次", async () => {
  const scheduler = createScheduler();
  const statusDocument = installPollingStatusDocument();
  const navigations = [];
  let loadCount = 0;
  const page = new GamePage({
    loadRoom: {
      async execute() {
        loadCount += 1;
        throw new ApiError("ROOM_NOT_FOUND", "找不到目前房間。", 404);
      },
    },
    navigate: (path) => navigations.push(path),
    schedule: scheduler.schedule,
    cancelSchedule: scheduler.cancel,
  });
  page.room = { id: "room-deleted", status: "COLLECTING_ACTIONS", version: 7 };

  try {
    page.startPolling();
    await assert.doesNotReject(scheduler.tasks[0].callback());
    await assert.doesNotReject(page.pollOnce());

    assert.equal(loadCount, 1, "停止後不得再次讀取已刪除的房間");
    assert.equal(page.pollingStopped, true);
    assert.equal(page.room, null, "不得保留已刪除房間的 canonical state");
    assert.equal(scheduler.tasks.length, 1, "收到第一個 404 後不得再排定 polling");
    assert.deepEqual(navigations, ["/"], "舊分頁只可導回首頁一次");
    assert.equal(statusDocument.pollingStatus.dataset.kind, "room-removed");
    assert.equal(
      statusDocument.pollingStatus.textContent,
      "房間已結束或刪除，已返回首頁。",
    );
  } finally {
    statusDocument.restore();
  }
});

test("GamePage 不把其他 404 誤判為房間已刪除", async () => {
  const page = new GamePage({
    loadRoom: {
      async execute() {
        throw new ApiError("PLAYER_NOT_FOUND", "找不到玩家。", 404);
      },
    },
    schedule: () => 1,
    cancelSchedule: () => {},
  });
  page.room = { status: "COLLECTING_ACTIONS", version: 7 };

  await assert.rejects(
    page.pollOnce(),
    (error) => error?.code === "PLAYER_NOT_FOUND",
  );
  assert.equal(page.pollingStopped, false);
  assert.notEqual(page.room, null);
});

test("GamePage 遇到 409 時立即重新載入 canonical state", async () => {
  const scheduler = createScheduler();
  const statusDocument = installPollingStatusDocument();
  const canonicalRoom = { status: "WAITING_FOR_ROLL", version: 9 };
  let loadCount = 0;
  let renderCount = 0;
  const page = new GamePage({
    loadRoom: {
      async execute() {
        loadCount += 1;
        if (loadCount === 1) {
          throw new ApiError("VERSION_CONFLICT", "狀態已更新", 409);
        }
        return canonicalRoom;
      },
    },
    schedule: scheduler.schedule,
    cancelSchedule: scheduler.cancel,
  });
  page.room = { status: "COLLECTING_ACTIONS", version: 7 };
  page.render = () => { renderCount += 1; };
  page.syncRoute = () => {};

  try {
    page.startPolling();
    await assert.doesNotReject(scheduler.tasks[0].callback());

    assert.equal(loadCount, 2, "409 後必須立即 reload，不等待下一個 timer");
    assert.strictEqual(page.room, canonicalRoom);
    assert.equal(renderCount, 1);
    assert.equal(scheduler.tasks[1].delay, 3000);
    assert.equal(statusDocument.pollingStatus.dataset.kind, "conflict-reloaded");
    assert.equal(statusDocument.pollingStatus.textContent, "資料已更新，已重新載入。");
  } finally {
    statusDocument.restore();
  }
});

test("遊戲頁提供不只依賴顏色的 polling live status", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");

  assert.match(html, /id=["']pollingStatus["']/);
  assert.match(html, /id=["']pollingStatus["'][^>]*role=["']status["']/);
  assert.match(html, /id=["']pollingStatus["'][^>]*aria-live=["']polite["']/);
});
