import { toRoomViewModel } from "../../adapters/presenters/room-view-model.js";

const byId = (id) => document.getElementById(id);

const WORLD_FIELD_ERRORS = {
  story_title: { inputId: "worldTitle", errorId: "worldTitleError" },
  premise: { inputId: "worldPremiseInput", errorId: "worldPremiseError" },
  objective: { inputId: "worldObjectiveInput", errorId: "worldObjectiveError" },
  opening_scene: { inputId: "openingSceneInput", errorId: "openingSceneError" },
  core_obstacle: { inputId: "coreObstacleInput", errorId: "coreObstacleError" },
};

function element(tagName, { className, text, title } = {}) {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  if (title) node.title = title;
  return node;
}

function publicErrorMessage(error, fallback) {
  return typeof error?.publicMessage === "string" && error.publicMessage.trim()
    ? error.publicMessage
    : fallback;
}

export class GamePage {
  constructor({
    loadRoom,
    createRoom,
    joinRoom,
    confirmWorld,
    generateWorld,
    startGame,
    updateCharacter,
    submitAction,
    rollRound,
    decideSpark,
    resolveRound,
    fallbackRound,
    finishGame,
    deleteRoom,
    apiMode = "mock",
    connectionLabel,
    persistenceLabel,
    navigate = null,
    schedule = (callback, delay) => globalThis.setTimeout(callback, delay),
    cancelSchedule = (id) => globalThis.clearTimeout(id),
    pollingIntervalMs = 3000,
  }) {
    this.useCases = {
      loadRoom,
      createRoom,
      joinRoom,
      confirmWorld,
      generateWorld,
      startGame,
      updateCharacter,
      submitAction,
      rollRound,
      decideSpark,
      resolveRound,
      fallbackRound,
      finishGame,
      deleteRoom,
    };
    this.apiMode = apiMode;
    this.connectionLabel = connectionLabel;
    this.persistenceLabel = persistenceLabel;
    this.navigate = navigate;
    this.schedule = schedule;
    this.cancelSchedule = cancelSchedule;
    this.pollingIntervalMs = pollingIntervalMs;
    this.room = null;
    this.pollTimer = null;
    this.pollInFlight = false;
    this.pollingStopped = false;
    this.pollFailureCount = 0;
    this.nextPollingDelayMs = pollingIntervalMs;
    this.busy = false;
  }

  async mount() {
    byId("connectionStatus").lastChild.textContent = ` ${this.connectionLabel}`;
    byId("persistenceStatus").textContent = this.persistenceLabel;
    byId("newRoomButton").addEventListener("click", () => this.handleCreateRoom());
    byId("resetButton").hidden = this.apiMode !== "mock";
    byId("resetButton").addEventListener("click", () => this.handleResetRoom());
    byId("joinForm").addEventListener("submit", (event) => this.handleJoin(event));
    byId("worldForm").addEventListener("submit", (event) => this.handleConfirmWorld(event));
    byId("generateWorldButton").addEventListener("click", (event) => this.handleGenerateWorld(event));
    byId("startGameButton").addEventListener("click", () => this.handleStartGame());
    byId("characterForm").addEventListener("submit", (event) => this.handleCharacter(event));
    ["courageInput", "insightInput", "bondInput"].forEach((id) => {
      byId(id).addEventListener("input", () => this.renderAttributePoints());
    });
    byId("toneInput").addEventListener("change", () => this.renderCustomTone());
    byId("actionForm").addEventListener("submit", (event) => this.handleAction(event));
    byId("rollRoundButton").addEventListener("click", () => this.handleRollRound());
    byId("useSparkButton").addEventListener("click", () => this.handleSpark("USE"));
    byId("declineSparkButton").addEventListener("click", () => this.handleSpark("DECLINE"));
    byId("resolveRoundButton").addEventListener("click", () => this.handleResolve(false));
    byId("skipAndResolveButton").addEventListener("click", () => this.handleResolve(true));
    byId("retryResolutionButton").addEventListener("click", () => this.handleResolve(false));
    byId("fallbackRoundButton").addEventListener("click", () => this.handleFallback());
    byId("finishNowButton").addEventListener("click", () => this.handleFinish("FINISH_NOW"));
    byId("continueButton").addEventListener("click", () => this.handleFinish("CONTINUE"));
    byId("deleteRoomButton").addEventListener("click", () => this.handleDeleteRoom());
    await this.run(() => this.useCases.loadRoom.execute());
    this.startPolling();
  }

  startPolling() {
    this.pollingStopped = false;
    this.pollFailureCount = 0;
    this.nextPollingDelayMs = this.pollingIntervalMs;
    this.schedulePolling();
  }

  stopPolling() {
    this.pollingStopped = true;
    if (this.pollTimer !== null) {
      this.cancelSchedule(this.pollTimer);
      this.pollTimer = null;
    }
  }

  schedulePolling() {
    if (
      this.pollingStopped
      || this.pollTimer !== null
      || this.room?.status === "COMPLETED"
    ) return;
    this.pollTimer = this.schedule(() => {
      this.pollTimer = null;
      return this.pollOnce();
    }, this.nextPollingDelayMs);
  }

  async pollOnce() {
    if (
      this.pollingStopped
      || this.pollInFlight
      || this.busy
      || this.room?.status === "COMPLETED"
    ) return false;
    this.pollInFlight = true;
    try {
      const room = await this.useCases.loadRoom.execute();
      this.applyPolledRoom(room);
      this.handlePollingSuccess();
      return true;
    } catch (error) {
      if (error?.status === 409) {
        try {
          const room = await this.useCases.loadRoom.execute();
          this.applyPolledRoom(room);
          this.resetPollingBackoff();
          this.showPollingStatus("資料已更新，已重新載入。", "conflict-reloaded");
          return true;
        } catch (reloadError) {
          error = reloadError;
        }
      }

      if (error?.status === 404 && error?.code === "ROOM_NOT_FOUND") {
        this.room = null;
        this.stopPolling();
        this.showPollingStatus(
          "房間已結束或刪除，已返回首頁。",
          "room-removed",
        );
        if (this.navigate) this.navigate("/");
        return false;
      }

      if (error?.status === 401 || error?.status === 403) {
        this.pollingStopped = true;
        this.showPollingStatus(
          "登入狀態已失效，請回首頁重新加入。",
          "session-expired",
        );
        return false;
      }

      if (error?.status === undefined || error?.status >= 500) {
        const retryDelayMs = this.advancePollingBackoff();
        this.showPollingStatus(
          `連線中斷，將在 ${retryDelayMs / 1000} 秒後重試。`,
          "offline",
        );
        return false;
      }

      throw error;
    } finally {
      this.pollInFlight = false;
      this.schedulePolling();
    }
  }

  applyPolledRoom(room) {
    this.room = room;
    this.syncRoute();
    this.render();
  }

  handlePollingSuccess() {
    const reconnected = this.pollFailureCount > 0;
    this.resetPollingBackoff();
    if (reconnected) {
      this.showPollingStatus("已重新連線，資料已同步。", "reconnected");
    } else {
      this.showPollingStatus("");
    }
  }

  advancePollingBackoff() {
    const retryDelaysMs = [this.pollingIntervalMs, 5000, 10000];
    const delayIndex = Math.min(this.pollFailureCount, retryDelaysMs.length - 1);
    this.pollFailureCount += 1;
    this.nextPollingDelayMs = retryDelaysMs[delayIndex];
    return this.nextPollingDelayMs;
  }

  resetPollingBackoff() {
    this.pollFailureCount = 0;
    this.nextPollingDelayMs = this.pollingIntervalMs;
  }

  showPollingStatus(message, kind = "") {
    const status = globalThis.document?.getElementById("pollingStatus");
    if (!status) return;
    status.hidden = !message;
    status.textContent = message;
    status.dataset.kind = kind;
  }

  async handleCreateRoom() {
    await this.run(() => this.useCases.createRoom.execute(), "已建立新房間。");
  }

  async handleResetRoom() {
    if (this.apiMode !== "mock") return false;
    if (!globalThis.window.confirm("要清除目前 Mock 房間並建立新房間嗎？")) return false;
    return this.handleCreateRoom();
  }

  async handleDeleteRoom() {
    const canDelete = this.apiMode === "http"
      && this.room?.status === "COMPLETED"
      && this.room?.session?.isHost;
    if (!canDelete) return false;
    const confirmed = globalThis.window.confirm(
      "此操作會永久刪除房間。僅房主可執行，且所有資料都無法復原。要繼續嗎？",
    );
    if (!confirmed) return false;
    this.setBusy(true);
    this.showFeedback("");
    try {
      await this.useCases.deleteRoom.execute();
      this.room = null;
      this.stopPolling();
      this.showFeedback("房間已永久刪除。", "success");
      if (this.navigate) this.navigate("/");
      return true;
    } catch (error) {
      this.showFeedback(error.message || "刪除失敗，請稍後再試。", "error");
      return false;
    } finally {
      this.setBusy(false);
    }
  }

  async handleJoin(event) {
    event.preventDefault();
    const nickname = byId("nickname");
    const role = byId("role");
    const completed = await this.run(
      () => this.useCases.joinRoom.execute({ nickname: nickname.value, role: role.value }),
      "玩家已加入房間。",
    );
    if (completed) {
      nickname.value = "";
      role.value = "";
    }
  }

  async handleConfirmWorld(event) {
    event.preventDefault();
    this.clearWorldFieldErrors();
    await this.run(
      () => this.useCases.confirmWorld.execute({
        storyTitle: byId("worldTitle").value,
        premise: byId("worldPremiseInput").value,
        objective: byId("worldObjectiveInput").value,
        openingScene: byId("openingSceneInput").value,
        coreObstacle: byId("coreObstacleInput").value,
        tone: byId("toneInput").value,
        customTone: byId("customToneInput").value,
        maxRounds: Number(byId("maxRoundsInput").value),
      }),
      "世界設定已確認，現在可以邀請玩家加入。",
      { onError: (error) => this.showWorldFieldErrors(error.fieldErrors) },
    );
  }

  clearWorldFieldErrors() {
    Object.values(WORLD_FIELD_ERRORS).forEach(({ inputId, errorId }) => {
      const input = byId(inputId);
      const error = byId(errorId);
      input?.removeAttribute("aria-invalid");
      if (error) {
        error.hidden = true;
        error.textContent = "";
      }
    });
  }

  showWorldFieldErrors(fieldErrors = {}) {
    Object.entries(fieldErrors).forEach(([field, message]) => {
      const target = WORLD_FIELD_ERRORS[field];
      if (!target) return;
      const input = byId(target.inputId);
      const error = byId(target.errorId);
      input?.setAttribute("aria-invalid", "true");
      if (error) {
        error.hidden = false;
        error.textContent = message;
      }
    });
  }

  async handleGenerateWorld(event) {
    event.preventDefault();
    const maxRoundsInput = byId("maxRoundsInput");
    const selectedMaxRounds = maxRoundsInput?.value;
    const completed = await this.run(
      () => this.useCases.generateWorld.execute({
        keywords: byId("worldKeywordsInput").value,
        tone: byId("toneInput").value,
        customTone: byId("customToneInput").value,
        supplementalRequest: byId("supplementalRequestInput").value,
      }),
      "世界草稿已生成，請編輯後再確認。",
      {
        feedbackId: "worldGenerationFeedback",
        pendingMessage: "正在生成世界草稿…",
      },
    );
    if (completed) {
      this.applyGeneratedWorldDraft();
      if (maxRoundsInput) maxRoundsInput.value = selectedMaxRounds;
    }
  }

  applyGeneratedWorldDraft() {
    const world = this.room?.world;
    if (!world) return;
    byId("worldTitle").value = world.storyTitle ?? "";
    byId("worldPremiseInput").value = world.premise ?? "";
    byId("worldObjectiveInput").value = world.objective ?? "";
    byId("openingSceneInput").value = world.openingScene ?? "";
    byId("coreObstacleInput").value = world.coreObstacle ?? "";
    byId("toneInput").value = world.tone ?? byId("toneInput").value;
    byId("customToneInput").value = world.customTone ?? "";
    byId("worldGenerationRemaining").textContent = `剩餘 ${Math.max(0, 2 - (this.room.worldGenerationCount ?? 0))} 次生成`;
  }

  async handleStartGame() {
    await this.run(() => this.useCases.startGame.execute(), "遊戲已開始。所有玩家可以提交行動。");
  }

  async handleCharacter(event) {
    event.preventDefault();
    await this.run(
      () => this.useCases.updateCharacter.execute({
        name: byId("characterName").value,
        background: byId("characterBackground").value,
        trait: byId("characterTrait").value,
        weakness: byId("characterWeakness").value,
        courage: byId("courageInput").value,
        insight: byId("insightInput").value,
        bond: byId("bondInput").value,
      }),
      "角色已儲存。",
      { errorMessage: "角色儲存失敗，請重新整理後再試。" },
    );
  }

  async handleAction(event) {
    event.preventDefault();
    const input = byId("actionInput");
    const completed = await this.run(
      () => this.useCases.submitAction.execute({
        text: input.value,
        approach: byId("actionApproach").value,
      }),
      "行動已提交。",
    );
    if (completed) input.value = "";
  }

  async handleRollRound() {
    await this.run(() => this.useCases.rollRound.execute(), "骰點已揭曉，等待星火結算。");
  }

  async handleSpark(decision) {
    const message = decision === "USE" ? "已使用 1 點星火。" : "已保留星火。";
    await this.run(() => this.useCases.decideSpark.execute({ decision }), message);
  }

  async handleResolve(skipPendingSpark) {
    await this.run(
      () => this.useCases.resolveRound.execute({ skipPendingSpark }),
      "本回合已結算，進入下一回合。",
    );
  }

  async handleFallback() {
    await this.run(
      () => this.useCases.fallbackRound.execute(),
      "已使用系統備援敘事完成本回合。",
    );
  }

  async handleFinish(decision) {
    const message = decision === "FINISH_NOW"
      ? "故事已完成。"
      : "完整成功已鎖定，繼續進行尾聲探索。";
    await this.run(() => this.useCases.finishGame.execute({ decision }), message);
  }

  async run(
    operation,
    successMessage = "",
    {
      onError = null,
      feedbackId = "feedback",
      pendingMessage = "",
      errorMessage = "操作失敗，請稍後再試。",
    } = {},
  ) {
    this.setBusy(true);
    this.showFeedback(pendingMessage, pendingMessage ? "pending" : "", feedbackId);
    try {
      this.room = await operation();
      this.syncRoute();
      this.render();
      this.showFeedback(successMessage, "success", feedbackId);
      return true;
    } catch (error) {
      onError?.(error);
      this.showFeedback(publicErrorMessage(error, errorMessage), "error", feedbackId);
      return false;
    } finally {
      this.setBusy(false);
      if (this.room) this.render();
    }
  }

  syncRoute() {
    if (!this.navigate || !this.room?.roomCode) return;
    let route;
    if (this.room.status === "DRAFT") route = "/host/setup";
    else if (this.room.status === "LOBBY") route = `/room/${this.room.roomCode}/lobby`;
    else if (this.room.status === "COMPLETED") route = `/room/${this.room.roomCode}/ending`;
    else route = `/room/${this.room.roomCode}/play`;
    this.navigate(route);
  }

  setBusy(busy) {
    this.busy = busy;
    document.querySelectorAll("button[type='submit'], #newRoomButton, #startGameButton, #rollRoundButton, #useSparkButton, #declineSparkButton, #resolveRoundButton, #skipAndResolveButton, #retryResolutionButton, #fallbackRoundButton, #finishNowButton, #continueButton, #deleteRoomButton, #generateWorldButton").forEach((button) => {
      button.disabled = busy;
    });
  }

  showFeedback(message, kind = "", feedbackId = "feedback") {
    const feedback = byId(feedbackId);
    if (!feedback) return;
    feedback.hidden = !message;
    feedback.textContent = message;
    feedback.dataset.kind = kind;
  }

  render() {
    const view = toRoomViewModel(this.room);
    byId("roomCode").textContent = view.roomCode;
    byId("roundNumber").textContent = view.roundLabel;
    byId("playerCount").textContent = view.playerCountLabel;
    byId("actionCount").textContent = view.completed;
    byId("progressText").textContent = view.progressLabel;
    byId("progressBar").style.width = `${view.progressPercent}%`;
    byId("aiStatus").textContent = view.aiStatus;
    byId("worldName").textContent = view.world.name;
    byId("worldPremise").textContent = view.world.premise;
    byId("storyTitle").textContent = view.world.storyTitle;
    byId("objectiveText").textContent = view.world.objective;
    byId("officialProgress").textContent = `${view.progressPoints}（${view.gameProgressPercent}%）`;
    byId("officialDanger").textContent = `${view.dangerPoints}（${view.dangerPercent}%）`;
    byId("gameProgressBar").style.width = `${view.gameProgressPercent}%`;
    byId("dangerBar").style.width = `${view.dangerPercent}%`;
    byId("actionForm").hidden = view.isCompleted || view.status === "COMPLETION_AVAILABLE";
    byId("endingPanel").hidden = !view.isCompleted;
    byId("endingResultText").textContent = view.endingResultLabel;
    byId("endingCostText").textContent = view.endingCostLabel;
    this.renderHostControls(view);
    this.renderPlayers(view.players, view.currentPlayerId, view.canSubmitAction, view.status);
    this.renderEntries(view.entries);
    this.renderDiceResults(view);
  }

  renderHostControls(view) {
    const worldForm = byId("worldForm");
    worldForm.hidden = !view.canEditWorld;
    byId("joinForm").hidden = !view.canJoin;
    byId("lobbyControls").hidden = !(view.isHost && view.status === "LOBBY");
    byId("startGameButton").disabled = !view.canStart;
    byId("characterForm").hidden = !view.canEditCharacter;
    byId("roundHostControls").hidden = !view.canRoll;
    byId("sparkControls").hidden = !view.canDecideSpark;
    byId("resolveRoundControls").hidden = !view.canResolve;
    byId("resolutionRecoveryControls").hidden = !(view.canRetryResolution || view.canUseFallback);
    byId("resolutionFailureText").textContent = `${view.resolutionFailureLabel}。固定骰子與星火判定已保留，尚未提交進度、危機或故事。`;
    byId("completionControls").hidden = !(view.canFinishNow || view.canContinue);
    const canDeleteRoom = this.apiMode === "http" && view.isHost && view.status === "COMPLETED";
    byId("deleteRoomControls").hidden = !canDeleteRoom;
    byId("deleteRoomButton").disabled = !canDeleteRoom;
    if (view.currentDiceResult) {
      const improves = view.currentDiceResult.baseTotal === 6 || view.currentDiceResult.baseTotal === 9;
      byId("sparkHint").textContent = improves
        ? "使用星火可讓本次結果提升一級。"
        : "使用星火會讓總值 +1，但目前不會提升結果級別。";
    }
    byId("lobbyReadyText").textContent = view.players.length < 3
      ? `還需要 ${3 - view.players.length} 位玩家；目前 ${view.readyTotal}/${view.players.length} 位完成角色。`
      : `目前 ${view.readyTotal}/${view.players.length} 位完成角色。全員完成後即可開始。`;
    if (view.canEditCharacter) {
      const current = view.players.find((player) => player.id === view.currentPlayerId);
      if (current?.character) {
        byId("characterName").value = current.character.name;
        byId("characterBackground").value = current.character.background;
        byId("characterTrait").value = current.character.trait;
        byId("characterWeakness").value = current.character.weakness;
        byId("courageInput").value = String(current.character.courage);
        byId("insightInput").value = String(current.character.insight);
        byId("bondInput").value = String(current.character.bond);
      }
      this.renderAttributePoints();
    }
    if (view.canEditWorld) {
      byId("maxRoundsInput").value = String(view.maxRounds ?? 6);
      byId("worldGenerationRemaining").textContent = `剩餘 ${Math.max(0, 2 - view.worldGenerationCount)} 次生成`;
      byId("generateWorldButton").disabled = this.busy || view.worldGenerationCount >= 2;
      this.renderCustomTone();
    }
  }

  renderCustomTone() {
    const custom = byId("toneInput").value === "custom";
    byId("customToneLabel").hidden = !custom;
    byId("customToneInput").hidden = !custom;
    byId("customToneInput").required = custom;
  }

  renderAttributePoints() {
    const spent = ["courageInput", "insightInput", "bondInput"]
      .map((id) => Number(byId(id).value) || 0)
      .reduce((total, value) => total + value, 0);
    const remaining = 3 - spent;
    byId("attributePoints").textContent = remaining === 0 ? "配點完成" : `剩餘 ${remaining} 點`;
    byId("attributePoints").dataset.invalid = remaining !== 0;
  }

  renderPlayers(players, currentPlayerId, canSubmitAction, status) {
    const listItems = players.map((player) => {
      const ready = status === "LOBBY" ? player.characterReady : player.hasSubmitted;
      const item = element("li", { className: `player-item${player.isActive ? " active" : ""}` });
      item.append(element("span", { className: "avatar", text: player.name.slice(0, 1) }));
      const identity = element("span");
      identity.append(
        element("span", { className: "player-name", text: player.name }),
        element("span", { className: "player-role", text: player.role }),
      );
      item.append(identity, element("span", {
        className: `ready-dot${ready ? " done" : ""}`,
        title: status === "LOBBY" ? (ready ? "角色已完成" : "角色未完成") : (ready ? "已提交" : "等待中"),
      }));
      return item;
    });
    byId("playerList").replaceChildren(...listItems);

    const options = players.filter((player) => player.id === currentPlayerId).map((player) => {
      const option = element("option", { text: `${player.name} · ${player.role}` });
      option.value = player.id;
      return option;
    });
    byId("activePlayer").replaceChildren(...options);
    if (currentPlayerId) byId("activePlayer").value = currentPlayerId;
    byId("activePlayer").disabled = !canSubmitAction;
    byId("actionInput").disabled = !canSubmitAction;
    byId("actionApproach").disabled = !canSubmitAction;

    const turns = players.map((player) => {
      const ready = status === "LOBBY" ? player.characterReady : player.hasSubmitted;
      const label = status === "LOBBY" ? (ready ? "角色完成 ✓" : "角色未完成") : (ready ? "已提交 ✓" : "等待行動");
      const row = element("div", { className: `turn-row${ready ? " done" : ""}` });
      row.append(
        element("span", { text: player.name }),
        element("span", { text: label }),
      );
      return row;
    });
    byId("turnList").replaceChildren(...turns);
  }

  renderDiceResults(view) {
    const labels = {
      SUCCESS: "成功",
      PARTIAL_SUCCESS: "部分成功",
      FAILURE: "失敗",
    };
    const approaches = { courage: "勇氣", insight: "洞察", bond: "羈絆" };
    const rows = view.diceResults.map((result) => {
      const row = element("div", { className: `dice-result ${result.result.toLowerCase()}` });
      row.append(
        element("strong", { text: result.playerName }),
        element("span", { text: `${result.dice.join(" + ")} + ${approaches[result.approach]} ${result.attributeValue} = ${result.finalTotal}` }),
        element("span", { text: `${labels[result.result]}｜進度 +${result.progressDelta}・危機 +${result.dangerDelta}` }),
        element("span", { text: `星火：${result.sparkDecision === "PENDING" ? "等待決策" : result.sparkDecision === "USE" ? "已使用" : "已保留"}` }),
      );
      return row;
    });
    byId("diceResults").replaceChildren(...rows);
    byId("diceSummary").textContent = rows.length
      ? `待結算：進度 +${view.pendingProgress}／危機 +${view.pendingDanger}`
      : "尚未擲骰";
  }

  renderEntries(entries) {
    const articles = entries.map((entry) => {
      const article = element("article", {
        className: `story-entry${entry.type === "action" ? " player-action" : ""}`,
      });
      const meta = element("div", { className: "entry-meta" });
      meta.append(
        element("strong", { text: entry.title }),
        element("span", { text: `ROUND ${String(entry.round).padStart(2, "0")}` }),
      );
      article.append(meta, element("p", { text: entry.text }));
      return article;
    });
    const feed = byId("storyFeed");
    feed.replaceChildren(...articles);
    feed.scrollTop = feed.scrollHeight;
  }
}
