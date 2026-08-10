import test from "node:test";
import assert from "node:assert/strict";

import { toRoomViewModel } from "../../src/adapters/presenters/room-view-model.js";


function room(overrides = {}) {
  return {
    roomCode: "ENDING",
    round: 3,
    maxRounds: 4,
    status: "COMPLETION_AVAILABLE",
    world: { name: "測試世界", storyTitle: "測試世界", premise: "背景", objective: "目標" },
    players: [],
    entries: [],
    diceResults: [],
    progressPoints: 18,
    dangerPoints: 9,
    targetPoints: 18,
    progressPercent: 100,
    dangerPercent: 50,
    endingResult: null,
    endingCost: null,
    successLocked: false,
    session: { isHost: true, principalType: "host" },
    ...overrides,
  };
}


test("提前完成 ViewModel 顯示正式百分比與房主選項", () => {
  const view = toRoomViewModel(room());

  assert.equal(view.gameProgressPercent, 100);
  assert.equal(view.dangerPercent, 50);
  assert.equal(view.canFinishNow, true);
  assert.equal(view.canContinue, true);
  assert.match(view.aiStatus, /選擇結束或繼續/);
});


test("完成狀態 ViewModel 提供結局與代價文字", () => {
  const view = toRoomViewModel(room({
    status: "COMPLETED",
    endingResult: "PARTIAL_SUCCESS",
    endingCost: "MAJOR",
  }));

  assert.equal(view.isCompleted, true);
  assert.equal(view.endingResultLabel, "部分成功");
  assert.equal(view.endingCostLabel, "重大代價");
  assert.match(view.aiStatus, /故事已完成/);
});


test("LLM 結算失敗只向房主顯示手動重試與 fallback", () => {
  const hostView = toRoomViewModel(room({
    status: "RESOLUTION_FAILED",
    resolutionFailureCode: "THROTTLED",
    resolutionAttempts: 2,
  }));
  const playerView = toRoomViewModel(room({
    status: "RESOLUTION_FAILED",
    resolutionFailureCode: "THROTTLED",
    resolutionAttempts: 2,
    session: { isHost: false, principalType: "player" },
  }));

  assert.equal(hostView.canRetryResolution, true);
  assert.equal(hostView.canUseFallback, true);
  assert.equal(playerView.canRetryResolution, false);
  assert.equal(playerView.canUseFallback, false);
  assert.match(hostView.aiStatus, /暫時忙碌/);
  assert.match(hostView.aiStatus, /2 次/);
});
