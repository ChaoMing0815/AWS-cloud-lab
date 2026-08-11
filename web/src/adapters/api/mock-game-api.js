import { GameApi } from "../../application/ports/game-api.js";
import { ApiError } from "./api-error.js";

const ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

function randomId() {
  return globalThis.crypto.randomUUID();
}

function randomRoomCode() {
  const values = new Uint8Array(6);
  globalThis.crypto.getRandomValues(values);
  return Array.from(values, (value) => ROOM_CODE_ALPHABET[value % ROOM_CODE_ALPHABET.length]).join("");
}

function clone(value) {
  return structuredClone(value);
}

function targetPoints(room) {
  const calculated = room.initialPlayerCount * 2 * Math.max(0, room.maxRounds - 1);
  return calculated || room.targetPoints || 0;
}

function pointsPercent(points, target) {
  if (target <= 0) return 0;
  return Math.min(100, Math.round(points / target * 100));
}

function updateProgressMetrics(room) {
  room.targetPoints = targetPoints(room);
  room.progressPercent = pointsPercent(room.progressPoints, room.targetPoints);
  room.dangerPercent = pointsPercent(room.dangerPoints, room.targetPoints);
}

function completeGame(room) {
  updateProgressMetrics(room);
  room.status = "COMPLETED";
  room.endingResult = room.progressPercent >= 100
    ? "FULL_SUCCESS"
    : room.progressPercent >= 60 ? "PARTIAL_SUCCESS" : "FAILURE";
  room.endingCost = room.dangerPercent >= 70
    ? "MAJOR"
    : room.dangerPercent >= 40 ? "SIGNIFICANT" : "LOW";
  room.entries.push({
    id: randomId(),
    type: "ending",
    title: "故事結局",
    round: room.round,
    text: `故事以 ${room.endingResult} 收束，並付出 ${room.endingCost} 代價；Mock 故事主持人沒有修改規則狀態。`,
  });
}

function baseRoom({ withDemoPlayers = false } = {}) {
  const players = withDemoPlayers
    ? [
      { id: randomId(), name: "昭銘", role: "總務部的新鮮人", action: "", characterReady: true },
      { id: randomId(), name: "凜", role: "冷靜的工程師", action: "", characterReady: true },
      { id: randomId(), name: "洛河", role: "人脈廣的企劃", action: "", characterReady: true },
    ]
    : [];

  const currentPlayer = players[0];
  return {
    id: randomId(),
    roomCode: withDemoPlayers ? "BONUS7" : randomRoomCode(),
    status: withDemoPlayers ? "COLLECTING_ACTIONS" : "DRAFT",
    version: 1,
    round: withDemoPlayers ? 4 : 1,
    world: withDemoPlayers
      ? {
        name: "年終尾牙作戰",
        storyTitle: "尾牙前的最後一份提案",
        premise: "公司臨時宣布加碼大獎，但抽獎資格取決於各部門能否完成最後一項共同任務。",
        objective: "在尾牙抽獎前完成跨部門提案，爭取加碼年終獎金。",
        openingScene: "尾牙開始前一小時，關鍵數據仍散落在三個部門手中。",
        coreObstacle: "預算表被印成抽獎箱封條，活動組拒絕重做。",
        tone: "workplace_satire",
        customTone: null,
      }
      : {
        name: "尚未命名",
        storyTitle: "尚未命名",
        premise: "",
        objective: "",
        openingScene: "",
        coreObstacle: "",
        tone: "light_comedy",
        customTone: null,
      },
    maxRounds: 6,
    initialPlayerCount: withDemoPlayers ? players.length : 0,
    progressPoints: 0,
    dangerPoints: 0,
    pendingProgress: 0,
    pendingDanger: 0,
    targetPoints: 0,
    progressPercent: 0,
    dangerPercent: 0,
    endingResult: null,
    endingCost: null,
    successLocked: false,
    worldGenerationCount: 0,
    diceResults: [],
    players,
    session: currentPlayer
      ? {
        principalType: "player",
        playerId: currentPlayer.id,
        csrfToken: "mock-csrf",
        isHost: false,
        hostCsrfToken: null,
      }
      : {
        principalType: "anonymous",
        playerId: null,
        csrfToken: null,
        isHost: false,
        hostCsrfToken: null,
      },
    entries: withDemoPlayers
      ? [
        {
          id: randomId(),
          type: "narrator",
          title: "故事主持人",
          round: 3,
          text: "尾牙開始前一小時，總經理臨時宣布：只要跨部門提案能在今晚通過，全體年終獎金就再加一個月。問題是，關鍵數據還散落在三個互不相讓的部門手中。",
        },
        {
          id: randomId(),
          type: "narrator",
          title: "故事主持人",
          round: 4,
          text: "最新版預算表被印成尾牙抽獎箱的封條。想拿到資料，你們得在不驚動主持人的情況下說服活動組重新製作封條。",
        },
      ]
      : [{
        id: randomId(),
        type: "narrator",
        title: "故事主持人",
        round: 1,
        text: "新房間已建立。邀請 3–5 位玩家加入，準備共同推進故事。",
      }],
  };
}

export class MockGameApi extends GameApi {
  constructor() {
    super();
    this.room = baseRoom({ withDemoPlayers: true });
  }

  async loadRoom() {
    return clone(this.room);
  }

  async createRoom() {
    this.room = baseRoom();
    this.room.session = {
      principalType: "host",
      playerId: null,
      csrfToken: "mock-host-csrf",
      isHost: true,
      hostCsrfToken: "mock-host-csrf",
    };
    return clone(this.room);
  }

  async confirmWorld(world) {
    if (!this.room.session?.isHost) {
      throw new ApiError("HOST_SESSION_REQUIRED", "需要有效的房主工作階段。", 401);
    }
    if (this.room.status !== "DRAFT") {
      throw new ApiError("WORLD_ALREADY_CONFIRMED", "世界設定已確認。", 409);
    }
    this.room.world = {
      name: world.storyTitle,
      storyTitle: world.storyTitle,
      premise: world.premise,
      objective: world.objective,
      openingScene: world.openingScene,
      coreObstacle: world.coreObstacle,
      tone: world.tone,
      customTone: world.customTone || null,
    };
    this.room.maxRounds = world.maxRounds;
    this.room.status = "LOBBY";
    this.room.version += 1;
    return clone(this.room);
  }

  async generateWorld({ keywords, tone, customTone, supplementalRequest }) {
    if (!this.room.session?.isHost) {
      throw new ApiError("HOST_SESSION_REQUIRED", "需要有效的房主工作階段。", 401);
    }
    if (this.room.status !== "DRAFT") {
      throw new ApiError("WORLD_ALREADY_CONFIRMED", "世界設定已確認。", 409);
    }
    if (this.room.worldGenerationCount >= 2) {
      throw new ApiError("WORLD_GENERATION_LIMIT", "世界生成次數已達上限。", 409);
    }
    const title = keywords.join("");
    this.room.world = {
      name: title,
      storyTitle: title,
      premise: `${title}的資料在夜班期間出現異常，玩家必須共同找出原因。`,
      objective: `完成與${keywords[0]}有關的共同任務。`,
      openingScene: `${keywords[0]}突然讓所有既有安排失效。`,
      coreObstacle: `${keywords.at(-1)}遮蔽了關鍵線索。`,
      tone,
      customTone: customTone || null,
    };
    this.room.worldGenerationCount += 1;
    this.room.version += 1;
    return clone(this.room);
  }

  async startGame() {
    if (!this.room.session?.isHost) {
      throw new ApiError("HOST_SESSION_REQUIRED", "需要有效的房主工作階段。", 401);
    }
    if (this.room.status !== "LOBBY" || this.room.players.length < 3) {
      throw new ApiError("ROOM_NOT_STARTABLE", "需要 3–5 位玩家才能開始。", 409);
    }
    if (this.room.players.some((player) => !player.characterReady)) {
      throw new ApiError("CHARACTERS_INCOMPLETE", "所有玩家都必須先完成角色。", 409);
    }
    this.room.status = "COLLECTING_ACTIONS";
    this.room.initialPlayerCount = this.room.players.length;
    updateProgressMetrics(this.room);
    this.room.version += 1;
    this.room.entries.push({
      id: randomId(),
      type: "narrator",
      title: "故事主持人",
      round: 1,
      text: this.room.world.openingScene,
    });
    return clone(this.room);
  }

  async joinRoom({ nickname, role }) {
    if (this.room.status !== "LOBBY") {
      throw new ApiError("ROOM_NOT_JOINABLE", "只有等待中的房間可以加入玩家。", 409);
    }
    if (this.room.players.length >= 5) {
      throw new ApiError("ROOM_FULL", "房間已達 5 人上限。", 409);
    }
    const duplicate = this.room.players.some(
      (player) => player.name.trim().toLocaleLowerCase() === nickname.trim().toLocaleLowerCase(),
    );
    if (duplicate) {
      throw new ApiError("NICKNAME_TAKEN", "這個暱稱已有人使用。", 409);
    }

    this.room.players.push({
      id: randomId(),
      name: nickname,
      role,
      action: "",
      characterReady: false,
      character: null,
    });
    const player = this.room.players[this.room.players.length - 1];
    this.room.session = {
      principalType: "player",
      playerId: player.id,
      csrfToken: "mock-player-csrf",
      isHost: this.room.session?.isHost ?? false,
      hostCsrfToken: this.room.session?.hostCsrfToken ?? null,
    };
    this.room.version += 1;
    return clone(this.room);
  }

  async updateCharacter(character) {
    if (this.room.status !== "LOBBY") {
      throw new ApiError("CHARACTER_NOT_EDITABLE", "只有等待中的房間可以編輯角色。", 409);
    }
    const playerId = this.room.session?.playerId;
    const player = this.room.players.find(({ id }) => id === playerId);
    if (!player) {
      throw new ApiError("PLAYER_SESSION_REQUIRED", "需要有效的玩家工作階段。", 401);
    }
    player.character = { ...character, spark: 1 };
    player.characterReady = true;
    player.role = character.name;
    this.room.version += 1;
    return clone(this.room);
  }

  async submitAction({ text, approach }) {
    if (!["COLLECTING_ACTIONS", "AWAITING_HOST"].includes(this.room.status)) {
      throw new ApiError("ACTION_NOT_ALLOWED", "目前不能提交行動。", 409);
    }
    const playerId = this.room.session?.playerId;
    const player = this.room.players.find(({ id }) => id === playerId);
    if (!player) {
      throw new ApiError("PLAYER_NOT_FOUND", "找不到這位玩家。", 404);
    }

    player.action = text;
    player.actionApproach = approach;
    this.room.entries = this.room.entries.filter(
      (entry) => !(entry.type === "action" && entry.round === this.room.round && entry.playerId === player.id),
    );
    this.room.entries.push({
      id: randomId(),
      type: "action",
      title: `${player.name} · ${player.role}`,
      round: this.room.round,
      text,
      playerId: player.id,
    });
    this.room.version += 1;

    if (this.room.players.length >= 3 && this.room.players.every(({ action }) => action)) {
      this.room.status = "AWAITING_HOST";
    } else {
      this.room.status = "COLLECTING_ACTIONS";
    }

    return clone(this.room);
  }

  async rollRound() {
    if (!this.room.session?.isHost) {
      throw new ApiError("HOST_SESSION_REQUIRED", "需要有效的房主工作階段。", 401);
    }
    if (this.room.status !== "AWAITING_HOST") {
      throw new ApiError("ROLL_NOT_ALLOWED", "尚未收齊行動，或本回合已擲骰。", 409);
    }
    const approachValues = { courage: 2, insight: 1, bond: 0 };
    this.room.diceResults = this.room.players.map((player, index) => {
      const dice = [[6, 6], [3, 3], [1, 1]][index] ?? [3, 4];
      const attributeValue = player.character?.[player.actionApproach]
        ?? approachValues[player.actionApproach]
        ?? 0;
      const finalTotal = dice[0] + dice[1] + attributeValue;
      const result = finalTotal >= 10 ? "SUCCESS" : finalTotal >= 7 ? "PARTIAL_SUCCESS" : "FAILURE";
      return {
        playerId: player.id,
        round: this.room.round,
        dice,
        approach: player.actionApproach,
        attributeValue,
        baseTotal: finalTotal,
        finalTotal,
        result,
        progressDelta: result === "SUCCESS" ? 2 : result === "PARTIAL_SUCCESS" ? 1 : 0,
        dangerDelta: result === "FAILURE" ? 2 : result === "PARTIAL_SUCCESS" ? 1 : 0,
        sparkUsed: 0,
        sparkDecision: (player.character?.spark ?? 1) > 0 ? "PENDING" : "DECLINE",
      };
    });
    this.room.pendingProgress = this.room.diceResults.reduce(
      (sum, result) => sum + result.progressDelta, 0,
    );
    this.room.pendingDanger = this.room.diceResults.reduce(
      (sum, result) => sum + result.dangerDelta, 0,
    );
    this.room.status = this.room.diceResults.every(({ sparkDecision }) => sparkDecision !== "PENDING")
      ? "RESOLVING"
      : "AWAITING_SPARK";
    this.room.version += 1;
    return clone(this.room);
  }

  async decideSpark({ decision }) {
    if (this.room.status !== "AWAITING_SPARK") {
      throw new ApiError("SPARK_NOT_ALLOWED", "目前不能提交星火決策。", 409);
    }
    const player = this.room.players.find(({ id }) => id === this.room.session?.playerId);
    const result = this.room.diceResults.find(({ playerId }) => playerId === player?.id);
    if (!player || !result) {
      throw new ApiError("PLAYER_SESSION_REQUIRED", "需要有效的玩家工作階段。", 401);
    }
    if (result.sparkDecision !== "PENDING") {
      throw new ApiError("SPARK_ALREADY_DECIDED", "本回合已完成星火決策。", 409);
    }
    const spark = player.character?.spark ?? 1;
    if (decision === "USE" && spark < 1) {
      throw new ApiError("SPARK_UNAVAILABLE", "角色目前沒有可用星火。", 409);
    }
    result.sparkDecision = decision;
    result.sparkUsed = decision === "USE" ? 1 : 0;
    result.finalTotal = result.baseTotal + result.sparkUsed;
    result.result = result.finalTotal >= 10
      ? "SUCCESS"
      : result.finalTotal >= 7 ? "PARTIAL_SUCCESS" : "FAILURE";
    result.progressDelta = result.result === "SUCCESS" ? 2 : result.result === "PARTIAL_SUCCESS" ? 1 : 0;
    result.dangerDelta = result.result === "FAILURE" ? 2 : result.result === "PARTIAL_SUCCESS" ? 1 : 0;
    this.room.pendingProgress = this.room.diceResults.reduce(
      (sum, item) => sum + item.progressDelta, 0,
    );
    this.room.pendingDanger = this.room.diceResults.reduce(
      (sum, item) => sum + item.dangerDelta, 0,
    );
    if (this.room.diceResults.every(({ sparkDecision }) => sparkDecision !== "PENDING")) {
      this.room.status = "RESOLVING";
    }
    this.room.version += 1;
    return clone(this.room);
  }

  async resolveRound({ skipPendingSpark = false } = {}) {
    if (!this.room.session?.isHost) {
      throw new ApiError("HOST_SESSION_REQUIRED", "需要有效的房主工作階段。", 401);
    }
    if (!["AWAITING_SPARK", "RESOLVING"].includes(this.room.status)) {
      throw new ApiError("RESOLVE_NOT_ALLOWED", "目前不能結算回合。", 409);
    }
    const pending = this.room.diceResults.filter(({ sparkDecision }) => sparkDecision === "PENDING");
    if (pending.length && !skipPendingSpark) {
      throw new ApiError("SPARK_DECISIONS_PENDING", "仍有玩家尚未完成星火決策。", 409);
    }
    pending.forEach((result) => { result.sparkDecision = "DECLINE"; });
    this.room.progressPoints += this.room.diceResults.reduce(
      (sum, result) => sum + result.progressDelta, 0,
    );
    this.room.dangerPoints += this.room.diceResults.reduce(
      (sum, result) => sum + result.dangerDelta, 0,
    );
    this.room.players.forEach((player) => {
      const result = this.room.diceResults.find(({ playerId }) => playerId === player.id);
      if (player.character && result) {
        player.character.spark -= result.sparkUsed;
        if (result.result === "FAILURE") {
          player.character.spark = Math.min(3, player.character.spark + 1);
        }
      }
      player.action = "";
      player.actionApproach = "";
    });
    const counts = this.room.diceResults.reduce(
      (summary, result) => ({ ...summary, [result.result]: summary[result.result] + 1 }),
      { SUCCESS: 0, PARTIAL_SUCCESS: 0, FAILURE: 0 },
    );
    this.room.entries.push({
      id: randomId(),
      type: "narrator",
      title: "故事主持人",
      round: this.room.round,
      text: `Mock 結算：${counts.SUCCESS} 次成功、${counts.PARTIAL_SUCCESS} 次部分成功、${counts.FAILURE} 次失敗。`,
    });
    this.room.pendingProgress = 0;
    this.room.pendingDanger = 0;
    updateProgressMetrics(this.room);
    if (this.room.round >= this.room.maxRounds) {
      completeGame(this.room);
    } else {
      this.room.round += 1;
      this.room.status = this.room.progressPercent >= 100
        ? "COMPLETION_AVAILABLE"
        : "COLLECTING_ACTIONS";
    }
    this.room.version += 1;
    return clone(this.room);
  }

  async finishGame({ decision }) {
    if (!this.room.session?.isHost) {
      throw new ApiError("HOST_SESSION_REQUIRED", "需要有效的房主工作階段。", 401);
    }
    if (this.room.status !== "COMPLETION_AVAILABLE") {
      throw new ApiError("FINISH_NOT_ALLOWED", "目前不能選擇結局。", 409);
    }
    this.room.successLocked = true;
    if (decision === "CONTINUE") {
      this.room.status = "COLLECTING_ACTIONS";
    } else {
      completeGame(this.room);
    }
    this.room.version += 1;
    return clone(this.room);
  }
}
