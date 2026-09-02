function safeMessage(error, fallback) {
  return typeof error?.publicMessage === "string" && error.publicMessage.trim()
    ? error.publicMessage
    : fallback;
}

function setFeedback(element, message, kind = "status") {
  element.textContent = message;
  element.dataset.kind = kind;
  element.hidden = false;
}

function makeElement(documentRef, tagName, options = {}) {
  const element = documentRef.createElement(tagName);
  if (options.id) element.id = options.id;
  if (options.className) element.className = options.className;
  if (options.textContent !== undefined) element.textContent = options.textContent;
  if (options.type) element.type = options.type;
  if (options.href) element.href = options.href;
  if (options.maxLength) element.maxLength = options.maxLength;
  if (options.rows) element.rows = options.rows;
  if (options.hidden !== undefined) element.hidden = options.hidden;
  if (options.disabled !== undefined) element.disabled = options.disabled;
  for (const [name, value] of Object.entries(options.attributes ?? {})) {
    element.setAttribute(name, value);
  }
  return element;
}

const RULE_TOPICS = [
  { id: "start", label: "開始遊戲", query: "如何開始遊戲？" },
  { id: "attributes", label: "角色屬性", query: "角色屬性如何分配？" },
  { id: "turns", label: "回合流程", query: "一個回合如何進行？" },
  { id: "dice", label: "骰點判定", query: "骰點如何判定結果？" },
  { id: "spark", label: "星火", query: "星火如何使用？" },
  { id: "ending", label: "進度／危機／結局", query: "進度、危機與結局如何判定？" },
];

export class SupportWidget {
  constructor({
    lookupSupportRule,
    createSupportReportDraft,
    canDraftReport = false,
    documentRef = document,
  }) {
    this.lookupSupportRule = lookupSupportRule;
    this.createSupportReportDraft = createSupportReportDraft;
    this.canDraftReport = canDraftReport;
    this.document = documentRef;
    this.ruleBusy = false;
    this.reportBusy = false;
    this.isOpen = false;
    this.isAvoidingControls = false;
    this.ruleHistory = [];
  }

  mount() {
    if (this.document.getElementById("supportWidgetRoot")) return;

    const root = makeElement(this.document, "aside", {
      id: "supportWidgetRoot",
      className: "support-widget",
      attributes: { "aria-label": "規則寵物助手" },
    });
    const toggle = makeElement(this.document, "button", {
      id: "supportWidgetToggle",
      className: "support-widget__toggle",
      type: "button",
      attributes: {
        "aria-controls": "supportWidgetDialog",
        "aria-expanded": "false",
        "aria-label": "開啟規則寵物助手",
      },
    });
    const slime = makeElement(this.document, "span", {
      className: "support-widget__slime",
      attributes: { "aria-hidden": "true" },
    });
    const petShadow = makeElement(this.document, "span", {
      id: "supportWidgetPetShadow",
      className: "support-widget__slime-shadow",
    });
    const petBody = makeElement(this.document, "span", {
      id: "supportWidgetPetBody",
      className: "support-widget__slime-body",
    });
    const petFace = makeElement(this.document, "span", {
      id: "supportWidgetPetFace",
      className: "support-widget__slime-face",
    });
    const petJellyBase = makeElement(this.document, "span", {
      id: "supportWidgetPetJellyBase",
      className: "support-widget__slime-jelly-base",
    });
    slime.append(petShadow, petJellyBase, petBody, petFace);
    const toggleLabel = makeElement(this.document, "span", {
      id: "supportWidgetPetHint",
      className: "support-widget__toggle-label",
      textContent: "問規則",
    });
    toggle.append(slime, toggleLabel);

    const panel = makeElement(this.document, "section", {
      id: "supportWidgetDialog",
      className: "support-widget__dialog",
      hidden: true,
      attributes: {
        role: "dialog",
        "aria-modal": "false",
        "aria-labelledby": "supportWidgetTitle",
      },
    });
    const header = makeElement(this.document, "header", {
      className: "support-widget__header",
    });
    const headingGroup = makeElement(this.document, "div");
    const eyebrow = makeElement(this.document, "span", {
      className: "support-widget__eyebrow",
      textContent: "BOUNDED SUPPORT",
    });
    const title = makeElement(this.document, "h2", {
      id: "supportWidgetTitle",
      textContent: "史萊姆規則寵物",
    });
    headingGroup.append(eyebrow, title);
    const close = makeElement(this.document, "button", {
      id: "supportWidgetClose",
      className: "support-widget__close",
      textContent: "×",
      type: "button",
      attributes: { "aria-label": "關閉規則寵物助手" },
    });
    header.append(headingGroup, close);

    const boundary = makeElement(this.document, "p", {
      id: "supportWidgetBoundary",
      className: "support-widget__boundary",
      textContent: "只有兩個固定功能：有來源的規則查詢，以及待確認問題草稿。每次都是獨立查詢，這不是自由對話 AI。",
    });

    const intentNav = makeElement(this.document, "div", {
      className: "support-widget__intents",
      attributes: { role: "tablist", "aria-label": "選擇固定支援功能" },
    });
    const ruleIntent = makeElement(this.document, "button", {
      id: "supportWidgetRuleIntent",
      className: "support-widget__intent is-active",
      textContent: "查規則",
      type: "button",
      attributes: {
        role: "tab",
        "aria-selected": "true",
        "aria-controls": "supportWidgetRuleView",
      },
    });
    const reportIntent = makeElement(this.document, "button", {
      id: "supportWidgetReportIntent",
      className: "support-widget__intent",
      textContent: "建草稿",
      type: "button",
      attributes: {
        role: "tab",
        "aria-selected": "false",
        "aria-controls": "supportWidgetReportView",
      },
    });
    intentNav.append(ruleIntent, reportIntent);

    const ruleView = this.buildRuleView();
    const reportView = this.buildReportView();
    panel.append(header, boundary, intentNav, ruleView, reportView);
    root.append(toggle, panel);
    this.document.body.append(root);

    this.toggle = toggle;
    this.panel = panel;
    this.closeButton = close;
    this.ruleIntent = ruleIntent;
    this.reportIntent = reportIntent;
    this.ruleView = ruleView;
    this.reportView = reportView;
    this.root = root;

    const view = this.document.defaultView;
    if (view?.addEventListener) {
      this.controlAvoidanceHandler = () => this.updateControlAvoidance();
      view.addEventListener("resize", this.controlAvoidanceHandler);
      view.addEventListener("scroll", this.controlAvoidanceHandler, { passive: true });
      if (view.requestAnimationFrame) view.requestAnimationFrame(this.controlAvoidanceHandler);
      else this.controlAvoidanceHandler();
    }

    toggle.addEventListener("click", () => this.toggleDialog());
    close.addEventListener("click", () => this.close());
    ruleIntent.addEventListener("click", () => this.setIntent("rules"));
    reportIntent.addEventListener("click", () => this.setIntent("report"));
    this.document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && this.isOpen) this.close();
    });
    this.setDraftCapability(this.canDraftReport);
  }

  buildRuleView() {
    const view = makeElement(this.document, "div", {
      id: "supportWidgetRuleView",
      className: "support-widget__view",
      attributes: { role: "tabpanel", "aria-labelledby": "supportWidgetRuleIntent" },
    });
    const topics = makeElement(this.document, "div", {
      id: "supportWidgetTopics",
      className: "support-widget__topics",
      attributes: { "aria-label": "規則主題捷徑" },
    });
    for (const topic of RULE_TOPICS) {
      const shortcut = makeElement(this.document, "button", {
        id: `supportWidgetTopic-${topic.id}`,
        className: "support-widget__topic",
        textContent: topic.label,
        type: "button",
      });
      shortcut.addEventListener("click", () => this.askTopic(topic.query));
      topics.append(shortcut);
    }
    const history = makeElement(this.document, "div", {
      id: "supportWidgetRuleHistory",
      className: "support-widget__history",
      attributes: {
        "aria-label": "本次開啟的規則問答紀錄",
        "aria-live": "polite",
      },
    });
    const form = makeElement(this.document, "form", { id: "supportWidgetRuleForm" });
    const label = makeElement(this.document, "label", {
      textContent: "匿名查詢遊戲規則",
      attributes: { for: "supportWidgetRuleMessage" },
    });
    const input = makeElement(this.document, "textarea", {
      id: "supportWidgetRuleMessage",
      maxLength: 500,
      rows: 3,
      attributes: { required: "", placeholder: "例如：星火什麼時候可以用？" },
    });
    const submit = makeElement(this.document, "button", {
      id: "supportWidgetRuleButton",
      className: "support-widget__submit",
      textContent: "查詢有來源的規則",
      type: "submit",
    });
    const status = makeElement(this.document, "p", {
      id: "supportWidgetRuleStatus",
      className: "support-widget__status",
      hidden: true,
      attributes: { role: "status", "aria-live": "polite" },
    });
    const answer = makeElement(this.document, "p", {
      id: "supportWidgetRuleAnswer",
      className: "support-widget__answer",
      hidden: true,
    });
    const citations = makeElement(this.document, "pre", {
      id: "supportWidgetRuleCitations",
      className: "support-widget__citations",
      hidden: true,
    });
    form.append(label, input, submit, status, answer, citations);
    form.addEventListener("submit", async (event) => this.handleRuleLookup(event));
    view.append(topics, history, form);
    return view;
  }

  buildReportView() {
    const view = makeElement(this.document, "div", {
      id: "supportWidgetReportView",
      className: "support-widget__view",
      hidden: true,
      attributes: { role: "tabpanel", "aria-labelledby": "supportWidgetReportIntent" },
    });
    const boundary = makeElement(this.document, "p", {
      id: "supportWidgetDraftBoundary",
      className: "support-widget__draft-boundary",
      textContent: "草稿尚未提交／需人工確認／不會對外提交。",
    });
    const capability = makeElement(this.document, "p", {
      id: "supportWidgetCapability",
      className: "support-widget__capability",
      attributes: { role: "note" },
    });
    const form = makeElement(this.document, "form", { id: "supportWidgetReportForm" });
    const label = makeElement(this.document, "label", {
      textContent: "問題描述",
      attributes: { for: "supportWidgetReportDescription" },
    });
    const input = makeElement(this.document, "textarea", {
      id: "supportWidgetReportDescription",
      maxLength: 2000,
      rows: 4,
      attributes: { required: "", placeholder: "請描述重現步驟與預期／實際結果" },
    });
    const submit = makeElement(this.document, "button", {
      id: "supportWidgetReportButton",
      className: "support-widget__submit support-widget__submit--secondary",
      textContent: "建立待確認草稿",
      type: "submit",
    });
    const status = makeElement(this.document, "p", {
      id: "supportWidgetReportStatus",
      className: "support-widget__status",
      hidden: true,
      attributes: { role: "status", "aria-live": "polite" },
    });
    const result = makeElement(this.document, "pre", {
      id: "supportWidgetReportResult",
      className: "support-widget__result",
      hidden: true,
    });
    form.append(label, input, submit, status, result);
    form.addEventListener("submit", async (event) => this.handleReportDraft(event));
    view.append(boundary, capability, form);
    return view;
  }

  setDraftCapability(canDraftReport) {
    this.canDraftReport = Boolean(canDraftReport);
    const description = this.document.getElementById("supportWidgetReportDescription");
    const button = this.document.getElementById("supportWidgetReportButton");
    const capability = this.document.getElementById("supportWidgetCapability");
    if (!description || !button || !capability) return;
    description.disabled = !this.canDraftReport;
    button.disabled = !this.canDraftReport;
    capability.textContent = this.canDraftReport
      ? "已驗證 Player session；只會建立 local_draft_only 待確認草稿。"
      : "建立草稿需要有效 Player session；匿名仍可查詢遊戲規則。";
  }

  setIntent(intent) {
    const showRules = intent === "rules";
    this.ruleView.hidden = !showRules;
    this.reportView.hidden = showRules;
    this.ruleIntent.setAttribute("aria-selected", String(showRules));
    this.reportIntent.setAttribute("aria-selected", String(!showRules));
    this.ruleIntent.className = `support-widget__intent${showRules ? " is-active" : ""}`;
    this.reportIntent.className = `support-widget__intent${showRules ? "" : " is-active"}`;
  }

  toggleDialog() {
    if (this.isOpen) this.close();
    else this.open();
  }

  open() {
    if (!this.isOpen) this.resetRuleHistory();
    this.isOpen = true;
    this.updateControlAvoidance();
    this.syncRootClass();
    this.panel.hidden = false;
    this.toggle.setAttribute("aria-expanded", "true");
    this.closeButton.focus();
  }

  close() {
    this.isOpen = false;
    this.updateControlAvoidance();
    this.syncRootClass();
    this.panel.hidden = true;
    this.toggle.setAttribute("aria-expanded", "false");
    this.toggle.focus();
  }

  syncRootClass() {
    this.root.className = [
      "support-widget",
      this.isOpen ? "is-open" : "",
      this.isAvoidingControls ? "is-avoiding-controls" : "",
    ].filter(Boolean).join(" ");
  }

  updateControlAvoidance() {
    const view = this.document.defaultView;
    const composer = this.document.getElementById("actionForm");
    const canMeasure = view
      && Number.isFinite(view.innerWidth)
      && Number.isFinite(view.innerHeight)
      && view.innerWidth <= 720
      && composer
      && !composer.hidden
      && typeof composer.getBoundingClientRect === "function";

    if (!canMeasure) {
      this.isAvoidingControls = false;
      this.root.style?.removeProperty("--support-widget-bottom");
      this.syncRootClass();
      return;
    }

    const rect = composer.getBoundingClientRect();
    const intersectsViewport = rect.height > 0 && rect.top < view.innerHeight && rect.bottom > 0;
    this.isAvoidingControls = intersectsViewport;
    if (intersectsViewport) {
      const safeBottom = Math.ceil(view.innerHeight - rect.top + 12);
      this.root.style?.setProperty("--support-widget-bottom", `${safeBottom}px`);
    } else {
      this.root.style?.removeProperty("--support-widget-bottom");
    }
    this.syncRootClass();
  }

  resetRuleHistory() {
    this.ruleHistory = [];
    const history = this.document.getElementById("supportWidgetRuleHistory");
    if (history) history.textContent = "";
  }

  renderRuleHistory() {
    const history = this.document.getElementById("supportWidgetRuleHistory");
    history.textContent = this.ruleHistory.flatMap((entry) => {
      const lines = [`你｜${entry.question}`, `規則寵物｜${entry.answer}`];
      if (entry.citations.length > 0) {
        lines.push(`來源｜${entry.citations.map((item) => `${item.ruleId}｜${item.title}`).join("、")}`);
      }
      return lines;
    }).join("\n");
  }

  async askTopic(query) {
    if (!this.isOpen) this.open();
    this.setIntent("rules");
    this.document.getElementById("supportWidgetRuleMessage").value = query;
    await this.handleRuleLookup({ preventDefault() {} });
  }

  async handleRuleLookup(event) {
    event.preventDefault();
    if (this.ruleBusy) return;
    const button = this.document.getElementById("supportWidgetRuleButton");
    const status = this.document.getElementById("supportWidgetRuleStatus");
    const answer = this.document.getElementById("supportWidgetRuleAnswer");
    const citations = this.document.getElementById("supportWidgetRuleCitations");
    this.ruleBusy = true;
    button.disabled = true;
    answer.hidden = true;
    citations.hidden = true;
    setFeedback(status, "正在查詢 allowlisted 規則…");
    const question = this.document.getElementById("supportWidgetRuleMessage").value;
    try {
      const result = await this.lookupSupportRule.execute({
        message: question,
      });
      answer.textContent = result.answer;
      answer.hidden = false;
      if (result.status === "supported" && result.citations.length > 0) {
        citations.textContent = result.citations
          .map((item) => `${item.ruleId}｜${item.title}｜${item.sourceSection}｜${item.sourceVersion}`)
          .join("\n");
        citations.hidden = false;
        setFeedback(status, "已找到有規則來源的答案。", "success");
      } else {
        citations.textContent = "";
        setFeedback(status, "規則資料不足，未進行猜測。", "unsupported");
      }
      this.ruleHistory.push({
        question,
        answer: result.answer,
        citations: result.status === "supported" ? result.citations : [],
      });
      this.renderRuleHistory();
    } catch (error) {
      setFeedback(status, safeMessage(error, "規則查詢暫時無法使用，請稍後再試。"), "error");
    } finally {
      this.ruleBusy = false;
      button.disabled = false;
    }
  }

  async handleReportDraft(event) {
    event.preventDefault();
    if (this.reportBusy || !this.canDraftReport) return;
    const button = this.document.getElementById("supportWidgetReportButton");
    const status = this.document.getElementById("supportWidgetReportStatus");
    const resultPanel = this.document.getElementById("supportWidgetReportResult");
    this.reportBusy = true;
    button.disabled = true;
    resultPanel.hidden = true;
    setFeedback(status, "正在建立待確認草稿…");
    try {
      const result = await this.createSupportReportDraft.execute({
        description: this.document.getElementById("supportWidgetReportDescription").value,
      });
      resultPanel.textContent = [
        `草稿編號：${result.reportId}`,
        `摘要：${result.summary}`,
        "尚未提交／需人工確認／不會對外提交。",
        `submissionStatus=${result.submissionStatus}`,
      ].join("\n");
      resultPanel.hidden = false;
      setFeedback(status, "待確認草稿已建立，仍未對外提交。", "success");
    } catch (error) {
      setFeedback(status, safeMessage(error, "問題草稿暫時無法建立，請稍後再試。"), "error");
    } finally {
      this.reportBusy = false;
      button.disabled = !this.canDraftReport;
    }
  }
}
