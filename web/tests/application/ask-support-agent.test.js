import test from "node:test";
import assert from "node:assert/strict";

let LookupSupportRule;
let CreateSupportReportDraft;
try {
  ({ LookupSupportRule, CreateSupportReportDraft } = await import(
    "../../src/application/use-cases/ask-support-agent.js"
  ));
} catch {
  LookupSupportRule = undefined;
  CreateSupportReportDraft = undefined;
}

test("規則查詢正規化 1–500 字元後只透過 SupportApi", async () => {
  assert.equal(typeof LookupSupportRule, "function", "LookupSupportRule 尚未建立");
  const commands = [];
  const useCase = new LookupSupportRule({
    async lookupRules(command) {
      commands.push(command);
      return { supported: false, answer: "目前資料不足。", citations: [] };
    },
  });

  await useCase.execute({ message: "  星火何時可以使用？  " });

  assert.deepEqual(commands, [{ message: "星火何時可以使用？" }]);
  await assert.rejects(useCase.execute({ message: "   " }), { code: "SUPPORT_MESSAGE_REQUIRED" });
  await assert.rejects(useCase.execute({ message: "規".repeat(501) }), {
    code: "SUPPORT_MESSAGE_TOO_LONG",
  });
});

test("問題草稿正規化 1–2000 字元且不接受前端 identity 或提交狀態", async () => {
  assert.equal(
    typeof CreateSupportReportDraft,
    "function",
    "CreateSupportReportDraft 尚未建立",
  );
  const commands = [];
  const useCase = new CreateSupportReportDraft({
    async createReportDraft(command) {
      commands.push(command);
      return {
        reportId: "report-opaque-1",
        requiresHumanConfirmation: true,
        submissionStatus: "local_draft_only",
      };
    },
  });

  await useCase.execute({
    description: "  重現：送出行動後畫面沒有更新。  ",
    playerId: "forged-player",
    identityHash: "forged-hash",
    submissionStatus: "submitted",
  });

  assert.deepEqual(commands, [{ description: "重現：送出行動後畫面沒有更新。" }]);
  await assert.rejects(useCase.execute({ description: "\n\t" }), {
    code: "SUPPORT_DESCRIPTION_REQUIRED",
  });
  await assert.rejects(useCase.execute({ description: "問".repeat(2001) }), {
    code: "SUPPORT_DESCRIPTION_TOO_LONG",
  });
});
