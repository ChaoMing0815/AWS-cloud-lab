import test from "node:test";
import assert from "node:assert/strict";

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
