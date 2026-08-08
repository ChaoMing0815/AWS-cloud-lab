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
  constructor({ loadRoom, createRoom, joinRoom, submitAction, connectionLabel, persistenceLabel }) {
    this.useCases = { loadRoom, createRoom, joinRoom, submitAction };
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
    byId("actionForm").addEventListener("submit", (event) => this.handleAction(event));
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

  async handleAction(event) {
    event.preventDefault();
    const input = byId("actionInput");
    const completed = await this.run(
      () => this.useCases.submitAction.execute({
        text: input.value,
      }),
      "行動已提交。",
    );
    if (completed) input.value = "";
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
    }
  }

  setBusy(busy) {
    document.querySelectorAll("button[type='submit'], #newRoomButton").forEach((button) => {
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
    this.renderPlayers(view.players, view.currentPlayerId, view.canSubmitAction);
    this.renderEntries(view.entries);
  }

  renderPlayers(players, currentPlayerId, canSubmitAction) {
    const listItems = players.map((player) => {
      const item = element("li", { className: `player-item${player.isActive ? " active" : ""}` });
      item.append(element("span", { className: "avatar", text: player.name.slice(0, 1) }));
      const identity = element("span");
      identity.append(
        element("span", { className: "player-name", text: player.name }),
        element("span", { className: "player-role", text: player.role }),
      );
      item.append(identity, element("span", {
        className: `ready-dot${player.hasSubmitted ? " done" : ""}`,
        title: player.hasSubmitted ? "已提交" : "等待中",
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

    const turns = players.map((player) => {
      const row = element("div", { className: `turn-row${player.hasSubmitted ? " done" : ""}` });
      row.append(
        element("span", { text: player.name }),
        element("span", { text: player.hasSubmitted ? "已提交 ✓" : "等待行動" }),
      );
      return row;
    });
    byId("turnList").replaceChildren(...turns);
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
