import { SupportApi } from "../../application/ports/support-api.js";
import { ApiError } from "./api-error.js";

const PUBLIC_ERRORS = new Map([
  ["SESSION_NOT_FOUND", [401, "目前的遊戲工作階段已失效。"]],
  ["PLAYER_SESSION_REQUIRED", [401, "需要有效的玩家工作階段。"]],
  ["CSRF_FAILED", [403, "CSRF 驗證失敗。"]],
  ["SUPPORT_REPORT_CONFLICT", [409, "問題草稿狀態衝突，請重新整理後再試。"]],
  ["REQUEST_VALIDATION_FAILED", [422, "請檢查輸入內容。"]],
  ["SUPPORT_RATE_LIMITED", [429, "操作過於頻繁，請稍後再試。"]],
  ["SUPPORT_UNAVAILABLE", [500, "客服暫時無法使用，請稍後再試。"]],
]);

function unavailable(status = 500) {
  return new ApiError(
    "SUPPORT_UNAVAILABLE",
    "客服暫時無法使用，請稍後再試。",
    status,
  );
}

function publicApiError(payload, status) {
  const code = payload?.error?.code;
  const mapping = PUBLIC_ERRORS.get(code);
  if (!mapping || mapping[0] !== status) return unavailable(status);
  return new ApiError(code, mapping[1], status);
}

function ruleResult(payload) {
  return {
    status: payload?.status,
    answer: payload?.answer,
    citations: Array.isArray(payload?.citations)
      ? payload.citations.map((citation) => ({
        ruleId: citation?.ruleId,
        title: citation?.title,
        sourceSection: citation?.sourceSection,
        sourceVersion: citation?.sourceVersion,
      }))
      : [],
  };
}

function reportResult(payload) {
  return {
    reportId: payload?.reportId,
    category: payload?.category,
    summary: payload?.summary,
    reproductionSteps: Array.isArray(payload?.reproductionSteps)
      ? [...payload.reproductionSteps]
      : [],
    expectedBehavior: payload?.expectedBehavior,
    actualBehavior: payload?.actualBehavior,
    requiresHumanConfirmation: payload?.requiresHumanConfirmation,
    submissionStatus: payload?.submissionStatus,
  };
}

export class FetchSupportApi extends SupportApi {
  constructor({
    basePath = "/api/v1",
    fetchImpl,
    idempotencyKeyFactory,
    playerSessionProvider,
  } = {}) {
    super();
    if (typeof basePath !== "string" || !basePath.startsWith("/") || basePath.startsWith("//")) {
      throw new ApiError("INVALID_SUPPORT_BASE_PATH", "客服 API 路徑設定無效。", 0);
    }
    this.basePath = basePath.replace(/\/$/, "");
    this.fetchImpl = fetchImpl ?? ((...args) => globalThis.fetch(...args));
    this.idempotencyKeyFactory = idempotencyKeyFactory ?? (() => globalThis.crypto.randomUUID());
    this.playerSessionProvider = playerSessionProvider ?? (async () => null);
  }

  async lookupRules({ message }) {
    const payload = await this.request("/support/rules:lookup", { message });
    return ruleResult(payload);
  }

  async createReportDraft({ description }) {
    const session = await this.playerSessionProvider();
    if (session?.principalType !== "player" || !session.csrfToken?.trim()) {
      throw new ApiError(
        "PLAYER_SESSION_REQUIRED",
        "需要有效的玩家工作階段。",
        401,
      );
    }
    const payload = await this.request("/support/reports:draft", { description }, {
      "X-CSRF-Token": session.csrfToken,
      "Idempotency-Key": this.idempotencyKeyFactory(),
    });
    return reportResult(payload);
  }

  async request(path, body, extraHeaders = {}) {
    let response;
    try {
      response = await this.fetchImpl(`${this.basePath}${path}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", ...extraHeaders },
        body: JSON.stringify(body),
      });
    } catch {
      throw unavailable();
    }

    let payload;
    try {
      payload = await response.json();
    } catch {
      throw unavailable(response.status || 500);
    }
    if (!response.ok) throw publicApiError(payload, response.status);
    return payload;
  }
}
