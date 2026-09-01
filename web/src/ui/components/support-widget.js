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
  }

  mount() {
    if (this.document.getElementById("supportWidgetRoot")) return;

    const root = makeElement(this.document, "aside", {
      id: "supportWidgetRoot",
      className: "support-widget",
      attributes: { "aria-label": "Support Agent" },
    });
    const toggle = makeElement(this.document, "button", {
      id: "supportWidgetToggle",
      className: "support-widget__toggle",
      type: "button",
      attributes: {
        "aria-controls": "supportWidgetDialog",
        "aria-expanded": "false",
        "aria-label": "開啟 Support Agent",
      },
    });
    const slime = makeElement(this.document, "span", {
      className: "support-widget__slime",
      attributes: { "aria-hidden": "true" },
    });
    const toggleLabel = makeElement(this.document, "span", {
      className: "support-widget__toggle-label",
      textContent: "支援",
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
      textContent: "史萊姆支援站",
    });
    headingGroup.append(eyebrow, title);
    const close = makeElement(this.document, "button", {
      id: "supportWidgetClose",
      className: "support-widget__close",
      textContent: "×",
      type: "button",
      attributes: { "aria-label": "關閉 Support Agent" },
    });
    header.append(headingGroup, close);

    const boundary = makeElement(this.document, "p", {
      id: "supportWidgetBoundary",
      className: "support-widget__boundary",
      textContent: "只有兩個固定功能：引用來源的規則查詢，以及待確認問題草稿。這不是自由對話 AI。",
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
    const fullPageLink = makeElement(this.document, "a", {
      className: "support-widget__full-page",
      href: "/support",
      textContent: "開啟完整支援頁",
    });
    panel.append(header, boundary, intentNav, ruleView, reportView, fullPageLink);
    root.append(toggle, panel);
    this.document.body.append(root);

    this.toggle = toggle;
    this.panel = panel;
    this.closeButton = close;
    this.ruleIntent = ruleIntent;
    this.reportIntent = reportIntent;
    this.ruleView = ruleView;
    this.reportView = reportView;

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
    view.append(form);
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
    this.isOpen = true;
    this.panel.hidden = false;
    this.toggle.setAttribute("aria-expanded", "true");
    this.closeButton.focus();
  }

  close() {
    this.isOpen = false;
    this.panel.hidden = true;
    this.toggle.setAttribute("aria-expanded", "false");
    this.toggle.focus();
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
    try {
      const result = await this.lookupSupportRule.execute({
        message: this.document.getElementById("supportWidgetRuleMessage").value,
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
