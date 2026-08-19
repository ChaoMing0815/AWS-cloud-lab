import { DomainError } from "../../domain/domain-error.js";

export class GenerateWorld {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  async execute({ keywords, tone, customTone = "", supplementalRequest = "" }) {
    const normalizedKeywords = String(keywords ?? "")
      .split(/[、，,]/)
      .map((keyword) => keyword.trim())
      .filter(Boolean);
    if (
      normalizedKeywords.length < 3
      || normalizedKeywords.length > 5
      || normalizedKeywords.some((keyword) => keyword.length > 20)
    ) {
      throw new DomainError("INVALID_WORLD_KEYWORDS", "請輸入 3–5 個、每個最多 20 字的關鍵字。", 422);
    }
    const normalizedCustomTone = String(customTone ?? "").trim();
    if ((tone === "custom" && !normalizedCustomTone) || (tone !== "custom" && normalizedCustomTone)) {
      throw new DomainError("INVALID_CUSTOM_TONE", "自訂調性設定不正確。", 422);
    }
    const normalizedSupplementalRequest = String(supplementalRequest ?? "").trim();
    if (normalizedSupplementalRequest.length > 200) {
      throw new DomainError("INVALID_SUPPLEMENTAL_REQUEST", "補充要求不可超過 200 字。", 422);
    }
    return this.gameApi.generateWorld({
      keywords: normalizedKeywords,
      tone,
      customTone: normalizedCustomTone || null,
      supplementalRequest: normalizedSupplementalRequest,
    });
  }
}
