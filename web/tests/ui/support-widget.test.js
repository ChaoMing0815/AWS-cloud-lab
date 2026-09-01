import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

let SupportWidget;
try {
  ({ SupportWidget } = await import("../../src/ui/components/support-widget.js"));
} catch {
  SupportWidget = undefined;
}

class FakeElement {
  constructor(tagName, documentRef) {
    this.tagName = tagName.toUpperCase();
    this.documentRef = documentRef;
    this.children = [];
    this.attributes = new Map();
    this.listeners = new Map();
    this.dataset = {};
    this.hidden = false;
    this.disabled = false;
    this.textContent = "";
    this.value = "";
    this.className = "";
    this.id = "";
  }

  append(...children) {
    this.children.push(...children);
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
  }

  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }

  addEventListener(type, handler) {
    const handlers = this.listeners.get(type) ?? [];
    handlers.push(handler);
    this.listeners.set(type, handlers);
  }

  async dispatch(type, event = {}) {
    for (const handler of this.listeners.get(type) ?? []) {
      await handler({ preventDefault() {}, ...event });
    }
  }

  focus() {
    this.documentRef.activeElement = this;
  }
}

function fakeDocument() {
  const documentRef = {
    activeElement: null,
    listeners: new Map(),
    createElement(tagName) {
      return new FakeElement(tagName, documentRef);
    },
    addEventListener(type, handler) {
      const handlers = this.listeners.get(type) ?? [];
      handlers.push(handler);
      this.listeners.set(type, handlers);
    },
    async dispatch(type, event = {}) {
      for (const handler of this.listeners.get(type) ?? []) await handler(event);
    },
    getElementById(id) {
      const visit = (node) => {
        if (node.id === id) return node;
        for (const child of node.children ?? []) {
          const found = visit(child);
          if (found) return found;
        }
        return null;
      };
      return visit(this.body) ?? visit(this.head);
    },
  };
  documentRef.body = new FakeElement("body", documentRef);
  documentRef.head = new FakeElement("head", documentRef);
  return documentRef;
}

function createWidget({ canDraftReport = false, ruleResult, reportResult } = {}) {
  assert.equal(typeof SupportWidget, "function", "SupportWidget 尚未建立");
  const documentRef = fakeDocument();
  const widget = new SupportWidget({
    lookupSupportRule: {
      async execute() {
        return ruleResult ?? {
          status: "unsupported",
          answer: "目前版本的規則資料沒有足夠證據回答這個問題。",
          citations: [],
        };
      },
    },
    createSupportReportDraft: {
      async execute() {
        return reportResult ?? {
          reportId: "draft-opaque-1",
          summary: "行動送出後畫面未更新",
          requiresHumanConfirmation: true,
          submissionStatus: "local_draft_only",
        };
      },
    },
    canDraftReport,
    documentRef,
  });
  widget.mount();
  return { documentRef, widget };
}

test("bootstrap 以同源 stylesheet 在全站掛載 bounded Support Widget", async () => {
  const bootstrap = await readFile(
    new URL("../../src/composition/bootstrap.js", import.meta.url),
    "utf8",
  );

  assert.match(bootstrap, /support-widget\.js/);
  assert.match(bootstrap, /\/support-widget\.css/);
  assert.match(bootstrap, /mountSupportWidget\(\)/);
  assert.doesNotMatch(bootstrap, /https?:\/\/|Bedrock|RAG|MCP|external.?submit/i);
});

test("Widget 提供可見開關、dialog 語意、Esc 關閉與 focus return", async () => {
  const { documentRef } = createWidget();
  const toggle = documentRef.getElementById("supportWidgetToggle");
  const panel = documentRef.getElementById("supportWidgetDialog");
  const close = documentRef.getElementById("supportWidgetClose");

  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.equal(toggle.getAttribute("aria-controls"), "supportWidgetDialog");
  assert.equal(panel.getAttribute("role"), "dialog");
  assert.equal(panel.getAttribute("aria-modal"), "false");
  assert.equal(panel.hidden, true);

  await toggle.dispatch("click");
  assert.equal(toggle.getAttribute("aria-expanded"), "true");
  assert.equal(panel.hidden, false);
  assert.equal(documentRef.activeElement, close);

  await documentRef.dispatch("keydown", { key: "Escape" });
  assert.equal(panel.hidden, true);
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.equal(documentRef.activeElement, toggle);
});

test("Widget 明確分離匿名規則查詢與 Player-only 問題草稿", async () => {
  const { documentRef } = createWidget({ canDraftReport: false });

  assert.match(documentRef.getElementById("supportWidgetBoundary").textContent, /固定功能/);
  assert.match(documentRef.getElementById("supportWidgetBoundary").textContent, /不是自由對話/);
  assert.equal(documentRef.getElementById("supportWidgetRuleButton").disabled, false);
  assert.equal(documentRef.getElementById("supportWidgetReportDescription").disabled, true);
  assert.equal(documentRef.getElementById("supportWidgetReportButton").disabled, true);
  assert.match(documentRef.getElementById("supportWidgetCapability").textContent, /Player.*session/);
  assert.match(documentRef.getElementById("supportWidgetDraftBoundary").textContent, /尚未提交/);
  assert.match(documentRef.getElementById("supportWidgetDraftBoundary").textContent, /需人工確認/);
  assert.match(documentRef.getElementById("supportWidgetDraftBoundary").textContent, /不會對外提交/);
});

test("Widget 規則結果只顯示 cited answer 或 unsupported不猜測", async () => {
  const { documentRef } = createWidget({
    ruleResult: {
      status: "supported",
      answer: "玩家可在看見骰點後決定是否使用星火。",
      citations: [{
        ruleId: "spark-usage",
        title: "星火",
        sourceSection: "4. 星火",
        sourceVersion: "mvp-v1",
      }],
    },
  });
  documentRef.getElementById("supportWidgetRuleMessage").value = "星火何時使用？";

  await documentRef.getElementById("supportWidgetRuleForm").dispatch("submit");

  assert.match(documentRef.getElementById("supportWidgetRuleAnswer").textContent, /看見骰點/);
  assert.match(documentRef.getElementById("supportWidgetRuleCitations").textContent, /spark-usage/);
  assert.match(documentRef.getElementById("supportWidgetRuleStatus").textContent, /規則來源/);
  assert.equal(documentRef.getElementById("supportWidgetRuleStatus").getAttribute("aria-live"), "polite");
});

test("Widget 草稿成功仍顯示 local_draft_only 三重安全語意", async () => {
  const { documentRef } = createWidget({ canDraftReport: true });
  documentRef.getElementById("supportWidgetReportDescription").value = "行動送出後畫面沒有更新。";

  await documentRef.getElementById("supportWidgetReportForm").dispatch("submit");

  const result = documentRef.getElementById("supportWidgetReportResult").textContent;
  assert.match(result, /尚未提交/);
  assert.match(result, /需人工確認/);
  assert.match(result, /不會對外提交/);
  assert.match(result, /local_draft_only/);
  assert.match(result, /draft-opaque-1/);
});

test("Widget CSS 支援像素角色、手機安全收合與 reduced-motion", async () => {
  const css = await readFile(
    new URL("../../support-widget.css", import.meta.url),
    "utf8",
  ).catch(() => "");

  assert.match(css, /image-rendering:\s*pixelated/);
  assert.match(css, /@media\s*\(max-width:\s*720px\)/);
  assert.match(css, /max-height:\s*(?:min|calc)/);
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
  assert.doesNotMatch(css, /@import|url\s*\(|https?:\/\//i);
});
