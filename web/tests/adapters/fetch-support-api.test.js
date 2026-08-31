import test from "node:test";
import assert from "node:assert/strict";

let FetchSupportApi;
try {
  ({ FetchSupportApi } = await import("../../src/adapters/api/fetch-support-api.js"));
} catch {
  FetchSupportApi = undefined;
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

test("規則查詢使用 same-origin cookie 與固定 endpoint", async () => {
  assert.equal(typeof FetchSupportApi, "function", "FetchSupportApi 尚未建立");
  let request;
  const api = new FetchSupportApi({
    basePath: "/api/v1",
    fetchImpl: async (url, options) => {
      request = { url, options };
      return jsonResponse({
        status: "supported",
        answer: "玩家可在看見骰點後決定是否使用星火。",
        citations: [{
          ruleId: "spark-usage",
          title: "星火",
          sourceSection: "4. 星火",
          sourceVersion: "2026-08-09",
        }],
      });
    },
  });

  const result = await api.lookupRules({ message: "星火何時可以使用？" });

  assert.equal(request.url, "/api/v1/support/rules:lookup");
  assert.equal(request.options.method, "POST");
  assert.equal(request.options.credentials, "include");
  assert.deepEqual(JSON.parse(request.options.body), { message: "星火何時可以使用？" });
  assert.equal(result.citations[0].ruleId, "spark-usage");
});

test("問題草稿只使用 canonical Player CSRF 且不送 identity 或提交狀態", async () => {
  const requests = [];
  const api = new FetchSupportApi({
    idempotencyKeyFactory: () => "support-draft-key",
    playerSessionProvider: async () => ({
      principalType: "player",
      playerId: "player-server-owned",
      csrfToken: "player-csrf",
      isHost: true,
      hostCsrfToken: "host-csrf-must-not-be-used",
    }),
    fetchImpl: async (url, options) => {
      requests.push({ url, options });
      return jsonResponse({
        reportId: "report-opaque-1",
        category: "general_issue",
        summary: "送出行動後沒有更新。",
        reproductionSteps: ["送出行動"],
        expectedBehavior: "畫面更新",
        actualBehavior: "畫面未更新",
        requiresHumanConfirmation: true,
        submissionStatus: "local_draft_only",
        identityHash: "must-not-leave-adapter",
      }, 201);
    },
  });

  const result = await api.createReportDraft({
    description: "送出行動後沒有更新。",
    playerId: "forged-player",
    identityHash: "forged-hash",
    submissionStatus: "submitted",
  });

  const request = requests[0];
  assert.equal(request.url, "/api/v1/support/reports:draft");
  assert.equal(request.options.headers["X-CSRF-Token"], "player-csrf");
  assert.equal(request.options.headers["Idempotency-Key"], "support-draft-key");
  assert.deepEqual(JSON.parse(request.options.body), { description: "送出行動後沒有更新。" });
  assert.deepEqual(result, {
    reportId: "report-opaque-1",
    category: "general_issue",
    summary: "送出行動後沒有更新。",
    reproductionSteps: ["送出行動"],
    expectedBehavior: "畫面更新",
    actualBehavior: "畫面未更新",
    requiresHumanConfirmation: true,
    submissionStatus: "local_draft_only",
  });
});

test("沒有 canonical Player session 時草稿 fail closed 且不發 request", async () => {
  for (const playerSession of [
    null,
    { principalType: "host", hostCsrfToken: "host-only" },
    { principalType: "player", playerId: "player-1" },
  ]) {
    let called = false;
    const api = new FetchSupportApi({
      playerSessionProvider: async () => playerSession,
      fetchImpl: async () => {
        called = true;
        return jsonResponse({});
      },
    });

    await assert.rejects(api.createReportDraft({ description: "畫面沒有更新。" }), {
      code: "PLAYER_SESSION_REQUIRED",
      status: 401,
    });
    assert.equal(called, false);
  }
});

test("adapter 拒絕跨來源 basePath", () => {
  assert.throws(
    () => new FetchSupportApi({ basePath: "https://example.invalid/api/v1" }),
    { code: "INVALID_SUPPORT_BASE_PATH" },
  );
  assert.throws(
    () => new FetchSupportApi({ basePath: "//example.invalid/api/v1" }),
    { code: "INVALID_SUPPORT_BASE_PATH" },
  );
});

test("401／403／409／422／429 與未知錯誤只產生固定安全訊息", async () => {
  const cases = [
    [401, "SESSION_NOT_FOUND", "目前的遊戲工作階段已失效。"],
    [401, "PLAYER_SESSION_REQUIRED", "需要有效的玩家工作階段。"],
    [403, "CSRF_FAILED", "CSRF 驗證失敗。"],
    [409, "SUPPORT_REPORT_CONFLICT", "問題草稿狀態衝突，請重新整理後再試。"],
    [422, "REQUEST_VALIDATION_FAILED", "請檢查輸入內容。"],
    [429, "SUPPORT_RATE_LIMITED", "操作過於頻繁，請稍後再試。"],
    [500, "SUPPORT_UNAVAILABLE", "客服暫時無法使用，請稍後再試。"],
  ];

  for (const [status, code, message] of cases) {
    const api = new FetchSupportApi({
      playerSessionProvider: async () => ({ principalType: "player", csrfToken: "csrf" }),
      fetchImpl: async () => jsonResponse({
        error: {
          code,
          message: "raw exception token=must-not-leak hash=must-not-leak",
        },
      }, status),
    });

    await assert.rejects(api.createReportDraft({ description: "問題描述" }), (error) => {
      assert.equal(error.code, code);
      assert.equal(error.status, status);
      assert.equal(error.message, message);
      assert.doesNotMatch(error.message, /raw|token|hash/i);
      return true;
    });
  }
});

test("網路 exception 與無效 JSON 不外洩 raw exception", async () => {
  const networkApi = new FetchSupportApi({
    fetchImpl: async () => { throw new Error("token=network-secret"); },
  });
  await assert.rejects(networkApi.lookupRules({ message: "星火" }), (error) => {
    assert.equal(error.message, "客服暫時無法使用，請稍後再試。");
    assert.doesNotMatch(error.message, /token|secret/i);
    return true;
  });

  const invalidJsonApi = new FetchSupportApi({
    fetchImpl: async () => new Response("raw stack and hash", { status: 502 }),
  });
  await assert.rejects(invalidJsonApi.lookupRules({ message: "星火" }), {
    code: "SUPPORT_UNAVAILABLE",
    message: "客服暫時無法使用，請稍後再試。",
  });
});
