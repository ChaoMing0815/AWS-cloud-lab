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

export class SupportPage {
  constructor({
    lookupSupportRule,
    createSupportReportDraft,
    canDraftReport,
    documentRef = document,
  }) {
    this.lookupSupportRule = lookupSupportRule;
    this.createSupportReportDraft = createSupportReportDraft;
    this.canDraftReport = canDraftReport;
    this.document = documentRef;
    this.ruleBusy = false;
    this.reportBusy = false;
  }

  mount() {
    this.document.getElementById("supportRuleForm")
      .addEventListener("submit", (event) => this.handleRuleLookup(event));
    this.document.getElementById("supportReportForm")
      .addEventListener("submit", (event) => this.handleReportDraft(event));

    const description = this.document.getElementById("supportReportDescription");
    const button = this.document.getElementById("supportReportButton");
    const capability = this.document.getElementById("supportReportCapability");
    description.disabled = !this.canDraftReport;
    button.disabled = !this.canDraftReport;
    capability.hidden = this.canDraftReport;
    capability.textContent = this.canDraftReport
      ? ""
      : "建立問題草稿需要有效的玩家工作階段；匿名仍可查詢遊戲規則。";
  }

  async handleRuleLookup(event) {
    event.preventDefault();
    if (this.ruleBusy) return;
    const button = this.document.getElementById("supportRuleButton");
    const feedback = this.document.getElementById("supportRuleFeedback");
    const answer = this.document.getElementById("supportRuleAnswer");
    const citations = this.document.getElementById("supportRuleCitations");
    this.ruleBusy = true;
    button.disabled = true;
    answer.hidden = true;
    citations.hidden = true;
    setFeedback(feedback, "正在查詢規則…");
    try {
      const result = await this.lookupSupportRule.execute({
        message: this.document.getElementById("supportRuleMessage").value,
      });
      answer.textContent = result.answer;
      answer.hidden = false;
      if (result.status === "supported" && result.citations.length > 0) {
        citations.textContent = result.citations
          .map((item) => `${item.ruleId}｜${item.title}｜${item.sourceSection}｜${item.sourceVersion}`)
          .join("\n");
        citations.hidden = false;
      }
      setFeedback(
        feedback,
        result.status === "supported" ? "已找到有規則依據的答案。" : "規則資料不足，未進行猜測。",
        "success",
      );
    } catch (error) {
      setFeedback(feedback, safeMessage(error, "規則查詢暫時無法使用，請稍後再試。"), "error");
    } finally {
      this.ruleBusy = false;
      button.disabled = false;
    }
  }

  async handleReportDraft(event) {
    event.preventDefault();
    if (this.reportBusy || !this.canDraftReport) return;
    const button = this.document.getElementById("supportReportButton");
    const feedback = this.document.getElementById("supportReportFeedback");
    const resultPanel = this.document.getElementById("supportReportResult");
    this.reportBusy = true;
    button.disabled = true;
    resultPanel.hidden = true;
    setFeedback(feedback, "正在建立本機草稿…");
    try {
      const result = await this.createSupportReportDraft.execute({
        description: this.document.getElementById("supportReportDescription").value,
      });
      resultPanel.textContent = [
        `草稿編號：${result.reportId}`,
        `摘要：${result.summary}`,
        "尚未提交、需要人工確認。",
        `requiresHumanConfirmation=${result.requiresHumanConfirmation}`,
        `submissionStatus=${result.submissionStatus}`,
      ].join("\n");
      resultPanel.hidden = false;
      setFeedback(feedback, "本機問題草稿已建立。", "success");
    } catch (error) {
      setFeedback(feedback, safeMessage(error, "問題草稿暫時無法建立，請稍後再試。"), "error");
    } finally {
      this.reportBusy = false;
      button.disabled = false;
    }
  }
}
