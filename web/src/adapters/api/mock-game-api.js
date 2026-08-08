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

  async submitAction({ text }) {
    if (this.room.status !== "COLLECTING_ACTIONS") {
      throw new ApiError("ACTION_NOT_ALLOWED", "目前不能提交行動。", 409);
    }
    const playerId = this.room.session?.playerId;
    const player = this.room.players.find(({ id }) => id === playerId);
    if (!player) {
      throw new ApiError("PLAYER_NOT_FOUND", "找不到這位玩家。", 404);
    }

    player.action = text;
    this.room.entries.push({
      id: randomId(),
      type: "action",
      title: `${player.name} · ${player.role}`,
      round: this.room.round,
      text,
    });
    this.room.version += 1;

    if (this.room.players.length >= 3 && this.room.players.every(({ action }) => action)) {
      const names = this.room.players.map(({ name }) => name).join("、");
      this.room.entries.push({
        id: randomId(),
        type: "narrator",
        title: "故事主持人",
        round: this.room.round,
        text: `${names} 的選擇串成一套完整方案。Mock 故事主持人已收到所有行動；正式骰子、星火與 LLM 結算將由後端 vertical slice 實作。`,
      });
      this.room.round += 1;
      this.room.players.forEach((item) => { item.action = ""; });
    }

    return clone(this.room);
  }
}
