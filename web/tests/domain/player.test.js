import test from "node:test";
import assert from "node:assert/strict";

import { normalizeNickname, normalizeRole } from "../../src/domain/player.js";

test("玩家輸入會去除前後空白", () => {
  assert.equal(normalizeNickname("  小明  "), "小明");
  assert.equal(normalizeRole("  細心的企劃  "), "細心的企劃");
});

test("空白或過長的玩家輸入會被拒絕", () => {
  assert.throws(() => normalizeNickname("   "), { code: "INVALID_NICKNAME" });
  assert.throws(() => normalizeNickname("1234567890123"), { code: "INVALID_NICKNAME" });
  assert.throws(() => normalizeRole(""), { code: "INVALID_ROLE" });
});
