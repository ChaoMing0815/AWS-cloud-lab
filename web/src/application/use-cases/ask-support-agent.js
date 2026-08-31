import { DomainError } from "../../domain/domain-error.js";

function normalizeBoundedText(value, { requiredCode, tooLongCode, maxLength, label }) {
  const normalized = typeof value === "string" ? value.trim() : "";
  if (!normalized) {
    throw new DomainError(requiredCode, `請輸入${label}。`);
  }
  if (normalized.length > maxLength) {
    throw new DomainError(tooLongCode, `${label}最多 ${maxLength} 個字元。`);
  }
  return normalized;
}

export class LookupSupportRule {
  constructor(supportApi) {
    this.supportApi = supportApi;
  }

  async execute({ message }) {
    return this.supportApi.lookupRules({
      message: normalizeBoundedText(message, {
        requiredCode: "SUPPORT_MESSAGE_REQUIRED",
        tooLongCode: "SUPPORT_MESSAGE_TOO_LONG",
        maxLength: 500,
        label: "規則問題",
      }),
    });
  }
}

export class CreateSupportReportDraft {
  constructor(supportApi) {
    this.supportApi = supportApi;
  }

  async execute({ description }) {
    return this.supportApi.createReportDraft({
      description: normalizeBoundedText(description, {
        requiredCode: "SUPPORT_DESCRIPTION_REQUIRED",
        tooLongCode: "SUPPORT_DESCRIPTION_TOO_LONG",
        maxLength: 2000,
        label: "問題描述",
      }),
    });
  }
}
