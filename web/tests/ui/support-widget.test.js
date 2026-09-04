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
    this.rect = { left: 0, right: 0, top: 0, bottom: 0, width: 0, height: 0 };
    this.styleValues = new Map();
    this.style = {
      setProperty: (name, value) => this.styleValues.set(name, value),
      removeProperty: (name) => this.styleValues.delete(name),
      getPropertyValue: (name) => this.styleValues.get(name) ?? "",
    };
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

  getBoundingClientRect() {
    return this.rect;
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
  documentRef.defaultView = {
    innerWidth: 390,
    innerHeight: 844,
    listeners: new Map(),
    addEventListener(type, handler) {
      const handlers = this.listeners.get(type) ?? [];
      handlers.push(handler);
      this.listeners.set(type, handlers);
    },
    requestAnimationFrame(callback) {
      callback();
    },
  };
  documentRef.body = new FakeElement("body", documentRef);
  documentRef.head = new FakeElement("head", documentRef);
  return documentRef;
}

function createWidget({ canDraftReport = false, ruleResult, reportResult } = {}) {
  assert.equal(typeof SupportWidget, "function", "SupportWidget 尚未建立");
  const documentRef = fakeDocument();
  const ruleQueries = [];
  const widget = new SupportWidget({
    lookupSupportRule: {
      async execute(input) {
        ruleQueries.push(input.message);
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
  return { documentRef, widget, ruleQueries };
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
  assert.match(documentRef.getElementById("supportWidgetRoot").className, /is-open/);

  await documentRef.dispatch("keydown", { key: "Escape" });
  assert.equal(panel.hidden, true);
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.equal(documentRef.activeElement, toggle);
  assert.doesNotMatch(documentRef.getElementById("supportWidgetRoot").className, /is-open/);
});

test("Widget launcher 以原創像素果凍史萊姆呈現，不帶恐龍或機器人輪廓", async () => {
  const { documentRef } = createWidget();
  const toggle = documentRef.getElementById("supportWidgetToggle");

  assert.equal(toggle.tagName, "BUTTON", "仍需保留原生 button 鍵盤與點擊語意");
  assert.ok(documentRef.getElementById("supportWidgetPetBody"));
  assert.ok(documentRef.getElementById("supportWidgetPetFace"));
  assert.ok(documentRef.getElementById("supportWidgetPetJellyBase"));
  assert.ok(documentRef.getElementById("supportWidgetPetShadow"));
  assert.equal(documentRef.getElementById("supportWidgetPetFeet"), null);
  assert.equal(documentRef.getElementById("supportWidgetPetHint").textContent, "問規則");

  const css = await readFile(
    new URL("../../support-widget.css", import.meta.url),
    "utf8",
  );
  const toggleRule = css.match(/\.support-widget__toggle\s*\{([^}]*)\}/)?.[1] ?? "";
  const petRule = css.match(/\.support-widget__slime\s*\{([^}]*)\}/)?.[1] ?? "";
  const bodyRule = css.match(/\.support-widget__slime-body\s*\{([^}]*)\}/)?.[1] ?? "";
  const faceRule = css.match(/\.support-widget__slime-face\s*\{([^}]*)\}/)?.[1] ?? "";
  const hintRule = css.match(/\.support-widget__toggle-label\s*\{([^}]*)\}/)?.[1] ?? "";

  assert.match(toggleRule, /width:\s*6(?:\.\d+)?rem/);
  assert.match(toggleRule, /height:\s*7(?:\.\d+)?rem/);
  assert.match(toggleRule, /padding:\s*0/);
  assert.match(toggleRule, /border:\s*0/);
  assert.match(toggleRule, /background:\s*transparent/);
  assert.match(toggleRule, /box-shadow:\s*none/);
  assert.match(petRule, /width:\s*5(?:\.\d+)?rem/);
  assert.match(petRule, /height:\s*6(?:\.\d+)?rem/);
  assert.match(bodyRule, /clip-path:\s*polygon\(/);
  assert.match(bodyRule, /border-radius:\s*0/);
  assert.match(bodyRule, /background:\s*(?:linear-gradient|rgba)/);
  assert.match(faceRule, /border:\s*0/);
  assert.match(faceRule, /background:\s*transparent/);
  assert.match(faceRule, /box-shadow:\s*none/);
  assert.doesNotMatch(css, /support-widget__slime-feet|dino|dinosaur|#102b31|#0a1b20/i);
  assert.match(hintRule, /position:\s*absolute/);
  assert.match(hintRule, /border-radius:\s*999px/);
});

test("Widget 在 mobile 核心 composer 進入 viewport 時停靠於控制區上方", () => {
  const { documentRef, widget } = createWidget();
  const composer = new FakeElement("form", documentRef);
  composer.id = "actionForm";
  composer.rect = { left: 25, right: 365, top: 567, bottom: 810, width: 340, height: 243 };
  documentRef.body.append(composer);

  widget.updateControlAvoidance();

  const root = documentRef.getElementById("supportWidgetRoot");
  assert.match(root.className, /is-avoiding-controls/);
  assert.equal(root.style.getPropertyValue("--support-widget-bottom"), "289px");
});

test("Widget 提供六類規則主題捷徑，並以同一 lookup 執行獨立查詢", async () => {
  const { documentRef, ruleQueries } = createWidget({
    ruleResult: {
      status: "supported",
      answer: "canonical answer",
      citations: [{
        ruleId: "rule-1",
        title: "開始遊戲",
        sourceSection: "MVP",
        sourceVersion: "mvp-v1",
      }],
    },
  });
  const topicIds = ["start", "attributes", "turns", "dice", "spark", "ending"];
  const labels = ["開始遊戲", "角色屬性", "回合流程", "骰點判定", "星火", "進度／危機／結局"];

  for (const [index, id] of topicIds.entries()) {
    const shortcut = documentRef.getElementById(`supportWidgetTopic-${id}`);
    assert.equal(shortcut.textContent, labels[index]);
  }

  await documentRef.getElementById("supportWidgetTopic-spark").dispatch("click");
  assert.deepEqual(ruleQueries, ["星火如何使用？"]);
});

test("Widget 在本次開啟期間保留可辨識問答與 citation，不暗示對話記憶", async () => {
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
  await documentRef.getElementById("supportWidgetToggle").dispatch("click");
  documentRef.getElementById("supportWidgetRuleMessage").value = "星火何時使用？";
  await documentRef.getElementById("supportWidgetRuleForm").dispatch("submit");

  const history = documentRef.getElementById("supportWidgetRuleHistory");
  assert.equal(history.getAttribute("aria-live"), "polite");
  assert.match(history.textContent, /你｜星火何時使用？/);
  assert.match(history.textContent, /規則寵物｜玩家可在看見骰點後/);
  assert.match(history.textContent, /spark-usage/);
  assert.match(documentRef.getElementById("supportWidgetBoundary").textContent, /每次都是獨立查詢/);
  assert.doesNotMatch(documentRef.getElementById("supportWidgetBoundary").textContent, /RAG|記得上一題/);
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

  const unsupported = createWidget();
  unsupported.documentRef.getElementById("supportWidgetRuleMessage").value = "規則沒有寫的內容";
  await unsupported.documentRef.getElementById("supportWidgetRuleForm").dispatch("submit");
  assert.match(
    unsupported.documentRef.getElementById("supportWidgetRuleStatus").textContent,
    /未進行猜測/,
  );
  assert.equal(
    unsupported.documentRef.getElementById("supportWidgetRuleCitations").hidden,
    true,
  );
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

test("Widget CSS 支援 viewport 底部寵物入口、開啟停跳與 reduced-motion", async () => {
  const css = await readFile(
    new URL("../../support-widget.css", import.meta.url),
    "utf8",
  ).catch(() => "");

  assert.match(css, /image-rendering:\s*pixelated/);
  const desktopWidgetRule = css.match(/\.support-widget\s*\{([^}]*)\}/)?.[1] ?? "";
  const baseDialogRule = css.match(/\.support-widget__dialog\s*\{([^}]*)\}/)?.[1] ?? "";
  assert.match(desktopWidgetRule, /right:\s*clamp\(3rem,\s*6vw,\s*6rem\)/);
  assert.match(baseDialogRule, /position:\s*absolute;/);
  assert.match(baseDialogRule, /bottom:\s*6\.75rem;/);
  assert.match(baseDialogRule, /max-height:\s*min\(68dvh,\s*36rem\);/);
  assert.match(
    baseDialogRule,
    /background:\s*color-mix\(in srgb,\s*var\(--night,\s*#071113\)\s*85%,\s*white\s*15%\);/,
    "dialog 背景需比主頁 night 色提高 15% 明度",
  );
  assert.match(css, /bottom:\s*max\([^;]*env\(safe-area-inset-bottom\)/);
  assert.match(css, /\.support-widget\.is-open\s+\.support-widget__slime[^}]*animation-play-state:\s*paused/s);
  assert.match(css, /@media\s*\(max-width:\s*720px\)/);
  const mobileCss = css.slice(
    css.indexOf("@media (max-width: 720px)"),
    css.indexOf("@media (prefers-reduced-motion: reduce)"),
  );
  const widgetRule = mobileCss.match(/\.support-widget\s*\{([^}]*)\}/)?.[1] ?? "";
  const landingWidgetRule = mobileCss.match(
    /body:has\(#landingPage:not\(\[hidden\]\)\)\s+\.support-widget\s*\{([^}]*)\}/,
  )?.[1] ?? "";
  const dialogRule = mobileCss.match(/\.support-widget__dialog\s*\{([^}]*)\}/)?.[1] ?? "";
  assert.match(widgetRule, /right:\s*1\.5rem;/);
  assert.match(widgetRule, /bottom:\s*max\([^;]*env\(safe-area-inset-bottom\)/);
  assert.match(
    landingWidgetRule,
    /bottom:\s*var\(--support-widget-bottom,\s*max\(10rem,\s*env\(safe-area-inset-bottom\)\)\);/,
  );
  assert.match(dialogRule, /bottom:\s*6\.75rem;/);
  assert.match(dialogRule, /max-height:\s*min\(62dvh,\s*32rem\);/);
  assert.match(
    mobileCss,
    /\.support-widget\.is-avoiding-controls\s+\.support-widget__dialog\s*\{[^}]*max-height:\s*min\(20dvh,\s*10rem\);/s,
  );

  const rootFont = 16;
  const viewport = { width: 390, height: 844 };
  const bottomRem = Number(widgetRule.match(/bottom:\s*max\(([\d.]+)rem/)?.[1]);
  const dialogBottomRem = Number(dialogRule.match(/bottom:\s*([\d.]+)rem/)?.[1]);
  const dialogDvh = Number(dialogRule.match(/max-height:\s*min\(([\d.]+)dvh/)?.[1]);
  const dialogMaxRem = Number(
    dialogRule.match(/max-height:\s*min\([\d.]+dvh,\s*([\d.]+)rem/)?.[1],
  );
  const avoidingDialogDvh = 20;
  const avoidingDialogMaxRem = 10;
  const mobileRight = Number(widgetRule.match(/right:\s*([\d.]+)rem/)?.[1]) * rootFont;
  const toggle = {
    left: viewport.width - mobileRight - 82,
    right: viewport.width - mobileRight,
    top: viewport.height - bottomRem * rootFont - 48,
    bottom: viewport.height - bottomRem * rootFont,
  };
  const landingDialog = {
    left: 0,
    right: viewport.width - mobileRight,
    bottom: viewport.height - bottomRem * rootFont - dialogBottomRem * rootFont,
    top: viewport.height - bottomRem * rootFont - dialogBottomRem * rootFont
      - Math.min(viewport.height * dialogDvh / 100, dialogMaxRem * rootFont),
  };
  const topbarNav = { left: 254.16, right: 372, top: 29, bottom: 46 };
  const composer = { left: 25, right: 365, top: 308, bottom: 550 };
  const avoidingBottom = Math.ceil(viewport.height - composer.top + 12);
  const avoidingDialog = {
    left: 0,
    right: viewport.width - mobileRight,
    bottom: viewport.height - avoidingBottom - dialogBottomRem * rootFont,
    top: viewport.height - avoidingBottom - dialogBottomRem * rootFont
      - Math.min(viewport.height * avoidingDialogDvh / 100, avoidingDialogMaxRem * rootFont),
  };
  const landingToggle = { left: 270, right: 366, top: 572, bottom: 684 };
  const landingNickname = { left: 36.6, right: 369, top: 761.9, bottom: 795.93 };
  const landingCreateButton = { left: 36.6, right: 369, top: 808.9, bottom: 852.93 };
  const overlaps = (first, second) => !(
    first.right <= second.left
    || first.left >= second.right
    || first.bottom <= second.top
    || first.top >= second.bottom
  );

  assert.equal(overlaps(toggle, topbarNav), false, "mobile toggle 不得與 topbar nav 相交");
  assert.equal(overlaps(landingToggle, landingNickname), false, "mobile landing toggle 不得遮擋暱稱輸入");
  assert.equal(overlaps(landingToggle, landingCreateButton), false, "mobile landing toggle 不得遮擋建立按鈕");
  assert.equal(overlaps(avoidingDialog, composer), false, "mobile dialog 不得遮擋 composer");
  assert.ok(landingDialog.left >= 0 && landingDialog.right <= viewport.width, "mobile dialog 不得水平溢位");
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)[\s\S]*animation:\s*none/);
  assert.doesNotMatch(css, /@import|url\s*\(|https?:\/\//i);
});

test("Widget 中尺寸與桌機在可展開時仍保留 composer 核心控制區", async () => {
  const css = await readFile(
    new URL("../../support-widget.css", import.meta.url),
    "utf8",
  );
  const overlap = (first, second) => !(
    first.right <= second.left
    || first.left >= second.right
    || first.bottom <= second.top
    || first.top >= second.bottom
  );
  const mediumRule = css.match(
    /@media\s*\(min-width:\s*721px\)\s*and\s*\(max-width:\s*1050px\)\s*\{[\s\S]*?\.support-widget__dialog\s*\{([^}]*)\}/,
  )?.[1] ?? "";
  const mediumGameWidgetRule = css.match(
    /@media\s*\(min-width:\s*721px\)\s*and\s*\(max-width:\s*1050px\)\s*\{[\s\S]*?body:has\(#gamePage:not\(\[hidden\]\)\)\s+\.support-widget\s*\{([^}]*)\}/,
  )?.[1] ?? "";
  const desktopGameRule = css.match(
    /@media\s*\(min-width:\s*1051px\)\s*\{[\s\S]*?body:has\(#gamePage:not\(\[hidden\]\)\)\s+\.support-widget__dialog\s*\{([^}]*)\}/,
  )?.[1] ?? "";

  assert.match(mediumRule, /max-height:\s*min\(45dvh,\s*25rem\);/);
  assert.doesNotMatch(mediumRule, /position:\s*fixed|top:\s*max|bottom:\s*auto/);
  assert.match(desktopGameRule, /position:\s*fixed;/);
  assert.match(desktopGameRule, /top:\s*auto;/);
  assert.match(desktopGameRule, /right:\s*0;/);
  assert.match(
    desktopGameRule,
    /bottom:\s*calc\(max\(1rem,\s*env\(safe-area-inset-bottom\)\)\s*\+\s*6\.75rem\);/,
  );
  assert.match(desktopGameRule, /width:\s*21rem;/);
  assert.match(
    mediumGameWidgetRule,
    /bottom:\s*var\(--support-widget-bottom,\s*max\(18rem,\s*env\(safe-area-inset-bottom\)\)\);/,
  );

  const mediumDialog = { left: 352, right: 752, top: 72, bottom: 252 };
  const mediumComposer = { left: 308.36, right: 727.63, top: 577, bottom: 810.09 };
  const mediumToggle = { left: 624, right: 720, top: 444, bottom: 556 };
  const desktopDialog = { left: 1024, right: 1424, top: 72, bottom: 252 };
  const desktopNickname = { left: 848.35, right: 1252.99, top: 314.1, bottom: 348.11 };
  const desktopCreateButton = { left: 848.35, right: 1252.99, top: 361.1, bottom: 403.61 };
  const desktopComposer = { left: 371.8, right: 1088.2, top: 579.41, bottom: 812.5 };
  assert.equal(overlap(mediumDialog, mediumComposer), false);
  assert.equal(overlap(mediumToggle, mediumComposer), false);
  assert.equal(overlap(desktopDialog, desktopComposer), false);
  assert.equal(overlap(desktopDialog, desktopNickname), false);
  assert.equal(overlap(desktopDialog, desktopCreateButton), false);
});
