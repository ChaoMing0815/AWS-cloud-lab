import { GameApi } from "../../application/ports/game-api.js";
import { ApiError } from "./api-error.js";

export class FetchGameApi extends GameApi {
  constructor({ basePath = "/api/v1", fetchImpl, idempotencyKeyFactory } = {}) {
    super();
    this.basePath = basePath.replace(/\/$/, "");
    this.fetchImpl = fetchImpl ?? ((...args) => globalThis.fetch(...args));
    this.idempotencyKeyFactory = idempotencyKeyFactory ?? (() => globalThis.crypto.randomUUID());
    this.room = null;
  }

  async loadRoom() {
    this.room = await this.request("/rooms/current");
    return this.room;
  }

  async createRoom() {
    this.room = await this.request("/rooms", { method: "POST", idempotent: true });
    return this.room;
  }

  async joinRoom({ nickname, role }) {
    this.requireRoom();
    this.room = await this.request(`/rooms/${this.room.id}/players`, {
      method: "POST",
      idempotent: true,
      body: {
        nickname,
        role,
        room_version: this.room.version,
      },
    });
    return this.room;
  }

  async confirmWorld(world) {
    this.requireRoom();
    this.room = await this.request(`/rooms/${this.room.id}/world`, {
      method: "PUT",
      idempotent: true,
      hostCsrfProtected: true,
      body: {
        story_title: world.storyTitle,
        premise: world.premise,
        objective: world.objective,
        opening_scene: world.openingScene,
        core_obstacle: world.coreObstacle,
        tone: world.tone,
        custom_tone: world.customTone || null,
        max_rounds: world.maxRounds,
        room_version: this.room.version,
      },
    });
    return this.room;
  }

  async startGame() {
    this.requireRoom();
    this.room = await this.request(`/rooms/${this.room.id}:start`, {
      method: "POST",
      idempotent: true,
      hostCsrfProtected: true,
      body: { room_version: this.room.version },
    });
    return this.room;
  }

  async updateCharacter(character) {
    this.requireRoom();
    this.room = await this.request(`/rooms/${this.room.id}/character`, {
      method: "PUT",
      idempotent: true,
      csrfProtected: true,
      body: {
        ...character,
        room_version: this.room.version,
      },
    });
    return this.room;
  }

  async submitAction({ text, approach }) {
    this.requireRoom();
    this.room = await this.request(
      `/rooms/${this.room.id}/rounds/${this.room.round}/action`,
      {
        method: "PUT",
        idempotent: true,
        csrfProtected: true,
        body: {
          text,
          approach,
          room_version: this.room.version,
        },
      },
    );
    return this.room;
  }

  async rollRound() {
    this.requireRoom();
    this.room = await this.request(
      `/rooms/${this.room.id}/rounds/${this.room.round}:roll`,
      {
        method: "POST",
        idempotent: true,
        hostCsrfProtected: true,
        body: { room_version: this.room.version },
      },
    );
    return this.room;
  }

  async decideSpark({ decision }) {
    this.requireRoom();
    this.room = await this.request(
      `/rooms/${this.room.id}/rounds/${this.room.round}/spark`,
      {
        method: "PUT",
        idempotent: true,
        csrfProtected: true,
        body: { decision, room_version: this.room.version },
      },
    );
    return this.room;
  }

  async resolveRound({ skipPendingSpark = false } = {}) {
    this.requireRoom();
    this.room = await this.request(
      `/rooms/${this.room.id}/rounds/${this.room.round}:resolve`,
      {
        method: "POST",
        idempotent: true,
        hostCsrfProtected: true,
        body: {
          skip_pending_spark: Boolean(skipPendingSpark),
          room_version: this.room.version,
        },
      },
    );
    return this.room;
  }

  async finishGame({ decision }) {
    this.requireRoom();
    this.room = await this.request(`/rooms/${this.room.id}:finish`, {
      method: "POST",
      idempotent: true,
      hostCsrfProtected: true,
      body: {
        decision,
        room_version: this.room.version,
      },
    });
    return this.room;
  }

  requireRoom() {
    if (!this.room) {
      throw new ApiError("ROOM_NOT_LOADED", "房間尚未載入。", 409);
    }
  }

  async request(
    path,
    {
      method = "GET",
      body,
      idempotent = false,
      csrfProtected = false,
      hostCsrfProtected = false,
    } = {},
  ) {
    const headers = body ? { "Content-Type": "application/json" } : {};
    if (idempotent) headers["Idempotency-Key"] = this.idempotencyKeyFactory();
    if (csrfProtected) {
      const csrfToken = this.room?.session?.csrfToken;
      if (!csrfToken) {
        throw new ApiError("CSRF_TOKEN_MISSING", "缺少 CSRF token，請重新載入。", 403);
      }
      headers["X-CSRF-Token"] = csrfToken;
    }
    if (hostCsrfProtected) {
      const csrfToken = this.room?.session?.hostCsrfToken;
      if (!csrfToken) {
        throw new ApiError("HOST_CSRF_TOKEN_MISSING", "缺少房主 CSRF token，請重新載入。", 403);
      }
      headers["X-CSRF-Token"] = csrfToken;
    }
    const response = await this.fetchImpl(`${this.basePath}${path}`, {
      method,
      credentials: "include",
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    let payload;
    try {
      payload = await response.json();
    } catch {
      throw new ApiError("INVALID_RESPONSE", "伺服器回傳無效資料。", response.status || 500);
    }

    if (!response.ok) {
      throw new ApiError(
        payload?.error?.code ?? "REQUEST_FAILED",
        payload?.error?.message ?? "API 操作失敗。",
        response.status,
      );
    }
    return payload;
  }
}
