import { toRoomViewModel } from "../../adapters/presenters/room-view-model.js";

const byId = (id) => document.getElementById(id);

function element(tagName, { className, text, title } = {}) {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  if (title) node.title = title;
  return node;
}

export class GamePage {
  constructor({
    loadRoom,
    createRoom,
    joinRoom,
    confirmWorld,
    startGame,
    updateCharacter,
    submitAction,
    rollRound,
    connectionLabel,
    persistenceLabel,
  }) {
    this.useCases = {
      loadRoom,
      createRoom,
      joinRoom,
      confirmWorld,
      startGame,
      updateCharacter,
      submitAction,
      rollRound,
    };
    this.connectionLabel = connectionLabel;
    this.persistenceLabel = persistenceLabel;
    this.room = null;
  }

  async mount() {
    byId("connectionStatus").lastChild.textContent = ` ${this.connectionLabel}`;
    byId("persistenceStatus").textContent = this.persistenceLabel;
    byId("newRoomButton").addEventListener("click", () => this.handleCreateRoom());
    byId("resetButton").addEventListener("click", () => {
      if (window.confirm("要清除目前 Mock 房間並建立新房間嗎？")) this.handleCreateRoom();
    });
    byId("joinForm").addEventListener("submit", (event) => this.handleJoin(event));
    byId("worldForm").addEventListener("submit", (event) => this.handleConfirmWorld(event));
    byId("startGameButton").addEventListener("click", () => this.handleStartGame());
    byId("characterForm").addEventListener("submit", (event) => this.handleCharacter(event));
    ["courageInput", "insightInput", "bondInput"].forEach((id) => {
      byId(id).addEventListener("input", () => this.renderAttributePoints());
    });
    byId("toneInput").addEventListener("change", () => this.renderCustomTone());
    byId("actionForm").addEventListener("submit", (event) => this.handleAction(event));
    byId("rollRoundButton").addEventListener("click", () => this.handleRollRound());
    await this.run(() => this.useCases.loadRoom.execute());
  }

  async handleCreateRoom() {
    await this.run(() => this.useCases.createRoom.execute(), "已建立新房間。");
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
    );
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

  async run(operation, successMessage = "") {
    this.setBusy(true);
    this.showFeedback("");
    try {
      this.room = await operation();
      this.render();
      this.showFeedback(successMessage, "success");
      return true;
    } catch (error) {
      this.showFeedback(error.message || "操作失敗，請稍後再試。", "error");
      return false;
    } finally {
      this.setBusy(false);
      if (this.room) this.render();
    }
  }

  setBusy(busy) {
    document.querySelectorAll("button[type='submit'], #newRoomButton, #startGameButton, #rollRoundButton").forEach((button) => {
      button.disabled = busy;
    });
  }

  showFeedback(message, kind = "") {
    const feedback = byId("feedback");
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
