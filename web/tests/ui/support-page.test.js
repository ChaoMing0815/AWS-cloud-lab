import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

let SupportPage;
try {
  ({ SupportPage } = await import("../../src/ui/pages/support-page.js"));
} catch {
  SupportPage = undefined;
}

function fakeElement(overrides = {}) {
  return {
    hidden: true,
    disabled: false,
    textContent: "",
    value: "",
    dataset: {},
    addEventListener() {},
    ...overrides,
  };
}

function fakeDocument() {
  const elements = {
    supportRuleForm: fakeElement(),
    supportRuleMessage: fakeElement(),
    supportRuleButton: fakeElement(),
    supportRuleFeedback: fakeElement(),
    supportRuleAnswer: fakeElement(),
    supportRuleCitations: fakeElement(),
    supportReportForm: fakeElement(),
    supportReportDescription: fakeElement(),
    supportReportButton: fakeElement(),
    supportReportCapability: fakeElement(),
    supportReportFeedback: fakeElement(),
    supportReportResult: fakeElement(),
  };
  return {
    elements,
    getElementById(id) {
      return elements[id];
    },
  };
}

test("完整 Support 頁從 production shell 與 route composition 退場", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");
  const bootstrap = await readFile(
    new URL("../../src/composition/bootstrap.js", import.meta.url),
    "utf8",
  );

  assert.doesNotMatch(html, /href=["']\/support["']|id=["']supportPage["']|id=["']supportRuleForm["']|id=["']supportReportForm["']/);
  assert.doesNotMatch(bootstrap, /path === ["']\/support["']|mountSupportPage|SupportPage/);
});

test("匿名仍可查規則，但問題草稿禁用並說明需要 Player session", () => {
  assert.equal(typeof SupportPage, "function", "SupportPage 尚未建立");
  const documentRef = fakeDocument();
  const page = new SupportPage({
    lookupSupportRule: { async execute() {} },
    createSupportReportDraft: { async execute() {} },
    canDraftReport: false,
    documentRef,
  });

  page.mount();

  assert.equal(documentRef.elements.supportRuleButton.disabled, false);
  assert.equal(documentRef.elements.supportReportDescription.disabled, true);
  assert.equal(documentRef.elements.supportReportButton.disabled, true);
  assert.equal(documentRef.elements.supportReportCapability.hidden, false);
  assert.match(documentRef.elements.supportReportCapability.textContent, /有效的玩家工作階段/);
});

test("規則查詢分別顯示安全答案與 citations 或固定 unsupported", async () => {
  const documentRef = fakeDocument();
  const answers = [
    {
      status: "supported",
      answer: "玩家可在看見骰點後決定是否使用星火。",
      citations: [{
        ruleId: "spark-usage",
        title: "星火",
        sourceSection: "4. 星火",
        sourceVersion: "2026-08-09",
      }],
    },
    {
      status: "unsupported",
      answer: "目前版本的規則資料沒有足夠證據回答這個問題。",
      citations: [],
    },
  ];
  const page = new SupportPage({
    lookupSupportRule: { async execute() { return answers.shift(); } },
    createSupportReportDraft: { async execute() {} },
    canDraftReport: false,
    documentRef,
  });

  documentRef.elements.supportRuleMessage.value = "星火何時使用？";
  await page.handleRuleLookup({ preventDefault() {} });
  assert.equal(
    documentRef.elements.supportRuleAnswer.textContent,
    "玩家可在看見骰點後決定是否使用星火。",
  );
  assert.match(documentRef.elements.supportRuleCitations.textContent, /spark-usage/);
  assert.match(documentRef.elements.supportRuleCitations.textContent, /星火/);

  documentRef.elements.supportRuleMessage.value = "規則沒有寫的內容";
  await page.handleRuleLookup({ preventDefault() {} });
  assert.equal(
    documentRef.elements.supportRuleAnswer.textContent,
    "目前版本的規則資料沒有足夠證據回答這個問題。",
  );
  assert.equal(documentRef.elements.supportRuleCitations.hidden, true);
});

test("成功草稿只顯示尚未提交、人工確認與 local_draft_only", async () => {
  const documentRef = fakeDocument();
  const page = new SupportPage({
    lookupSupportRule: { async execute() {} },
    createSupportReportDraft: {
      async execute() {
        return {
          reportId: "report-opaque-1",
          requiresHumanConfirmation: true,
          submissionStatus: "local_draft_only",
          identityHash: "must-not-render",
          runtimeToken: "must-not-render",
        };
      },
    },
    canDraftReport: true,
    documentRef,
  });
  page.mount();
  documentRef.elements.supportReportDescription.value = "送出行動後沒有更新。";

  await page.handleReportDraft({ preventDefault() {} });

  const visible = documentRef.elements.supportReportResult.textContent;
  assert.match(visible, /尚未提交/);
  assert.match(visible, /需要人工確認/);
  assert.match(visible, /local_draft_only/);
  assert.match(visible, /report-opaque-1/);
  assert.doesNotMatch(visible, /must-not-render/);
  assert.equal(documentRef.elements.supportReportResult.hidden, false);
});

test("UI 對 401／403／409／429 與未知 exception 顯示安全下一步", async () => {
  const cases = [
    [401, "需要有效的玩家工作階段。"],
    [403, "CSRF 驗證失敗。"],
    [409, "問題草稿狀態衝突，請重新整理後再試。"],
    [429, "操作過於頻繁，請稍後再試。"],
    [500, "問題草稿暫時無法建立，請稍後再試。"],
  ];

  for (const [status, expected] of cases) {
    const documentRef = fakeDocument();
    const page = new SupportPage({
      lookupSupportRule: { async execute() {} },
      createSupportReportDraft: {
        async execute() {
          const error = new Error("raw exception token=must-not-leak hash=must-not-leak");
          error.status = status;
          if (status !== 500) error.publicMessage = expected;
          throw error;
        },
      },
      canDraftReport: true,
      documentRef,
    });
    documentRef.elements.supportReportDescription.value = "問題描述";

    await page.handleReportDraft({ preventDefault() {} });

    assert.equal(documentRef.elements.supportReportFeedback.textContent, expected);
    assert.doesNotMatch(documentRef.elements.supportReportFeedback.textContent, /raw|token|hash/i);
    assert.equal(documentRef.elements.supportReportFeedback.hidden, false);
  }
});
