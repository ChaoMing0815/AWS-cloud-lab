const STORAGE_KEY = "co-story-project-demo-v1";

const seedState = () => ({
  roomCode: "BONUS7",
  round: 4,
  players: [
    { id: crypto.randomUUID(), name: "昭銘", role: "總務部的新鮮人", action: "" },
    { id: crypto.randomUUID(), name: "凜", role: "冷靜的工程師", action: "" },
    { id: crypto.randomUUID(), name: "洛河", role: "人脈廣的企劃", action: "" },
  ],
  entries: [
    {
      type: "narrator",
      title: "故事主持人",
      round: 3,
      text: "尾牙開始前一小時，總經理臨時宣布：只要跨部門提案能在今晚通過，全體年終獎金就再加一個月。問題是，關鍵數據還散落在三個互不相讓的部門手中。",
    },
    {
      type: "action",
      title: "昭銘 · 總務部的新鮮人",
      round: 3,
      text: "我先去茶水間找熟悉各部門八卦的同事，確認誰手上握有最新版預算表。",
    },
    {
      type: "narrator",
      title: "故事主持人",
      round: 4,
      text: "消息很快拼成一條奇怪線索：最新版預算表沒有遺失，而是被列印成尾牙抽獎箱的封條。想拿到資料，你們得在不驚動主持人的情況下說服活動組重新製作封條。",
    },
  ],
});

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return saved?.players?.length ? saved : seedState();
  } catch {
    return seedState();
  }
}

let state = loadState();

const el = (id) => document.getElementById(id);
const roomCode = el("roomCode");
const roundNumber = el("roundNumber");
const playerCount = el("playerCount");
const playerList = el("playerList");
const activePlayer = el("activePlayer");
const storyFeed = el("storyFeed");
const actionCount = el("actionCount");
const progressText = el("progressText");
const progressBar = el("progressBar");
const turnList = el("turnList");
const aiStatus = el("aiStatus");

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function escapeHtml(value) {
  return value.replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[character]);
}

function render() {
  const completed = state.players.filter((player) => player.action).length;
  roomCode.textContent = state.roomCode;
  roundNumber.textContent = String(state.round).padStart(2, "0");
  playerCount.textContent = `${state.players.length} / 5`;
  actionCount.textContent = completed;
  progressText.textContent = `${completed} / ${state.players.length}`;
  progressBar.style.width = `${(completed / state.players.length) * 100}%`;
  aiStatus.textContent = completed === state.players.length
    ? "正在整合所有玩家的選擇……"
    : `還有 ${state.players.length - completed} 位玩家尚未提交。`;

  playerList.innerHTML = state.players.map((player, index) => `
    <li class="player-item ${index === 0 ? "active" : ""}">
      <span class="avatar">${escapeHtml(player.name.slice(0, 1))}</span>
      <span><span class="player-name">${escapeHtml(player.name)}</span><span class="player-role">${escapeHtml(player.role)}</span></span>
      <span class="ready-dot ${player.action ? "done" : ""}" title="${player.action ? "已提交" : "等待中"}"></span>
    </li>
  `).join("");

  const selected = activePlayer.value;
  activePlayer.innerHTML = state.players.map((player) => `<option value="${player.id}">${escapeHtml(player.name)} · ${escapeHtml(player.role)}</option>`).join("");
  if (state.players.some((player) => player.id === selected)) activePlayer.value = selected;

  turnList.innerHTML = state.players.map((player) => `
    <div class="turn-row ${player.action ? "done" : ""}"><span>${escapeHtml(player.name)}</span><span>${player.action ? "已提交 ✓" : "等待行動"}</span></div>
  `).join("");

  storyFeed.innerHTML = state.entries.map((entry) => `
    <article class="story-entry ${entry.type === "action" ? "player-action" : ""}">
      <div class="entry-meta"><strong>${escapeHtml(entry.title)}</strong><span>ROUND ${String(entry.round).padStart(2, "0")}</span></div>
      <p>${escapeHtml(entry.text)}</p>
    </article>
  `).join("");
  storyFeed.scrollTop = storyFeed.scrollHeight;
}

function narratorText(actions) {
  const names = actions.map(({ name }) => name).join("、");
  return `${names} 的選擇意外串成一套完整方案。當投影片終於出現在會議室螢幕上，總經理卻提出最後條件：必須在尾牙主持人上台前，找出一位願意替全體同事背書的主管。你們要分頭遊說，還是冒險直接上台公開提案？`;
}

function completeRoundIfReady() {
  if (!state.players.every((player) => player.action)) return;
  const actions = state.players.map(({ name, action }) => ({ name, action }));
  window.setTimeout(() => {
    state.entries.push({ type: "narrator", title: "故事主持人", round: state.round, text: narratorText(actions) });
    state.round += 1;
    state.players.forEach((player) => { player.action = ""; });
    saveState();
    render();
  }, 650);
}

el("actionForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const player = state.players.find(({ id }) => id === activePlayer.value);
  const input = el("actionInput");
  const action = input.value.trim();
  if (!player || !action) return;
  player.action = action;
  state.entries.push({ type: "action", title: `${player.name} · ${player.role}`, round: state.round, text: action });
  input.value = "";
  saveState();
  render();
  completeRoundIfReady();
});

el("joinForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const nickname = el("nickname").value.trim();
  const role = el("role").value;
  if (!nickname || !role || state.players.length >= 5) return;
  state.players.push({ id: crypto.randomUUID(), name: nickname, role, action: "" });
  el("nickname").value = "";
  el("role").value = "";
  saveState();
  render();
});

el("newRoomButton").addEventListener("click", () => {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  state = seedState();
  state.roomCode = Array.from({ length: 6 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join("");
  saveState();
  render();
});

el("resetButton").addEventListener("click", () => {
  if (!window.confirm("要清除目前房間並恢復展示資料嗎？")) return;
  state = seedState();
  saveState();
  render();
});

render();
