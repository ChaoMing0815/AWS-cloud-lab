import { normalizeNickname, normalizeRole } from "../../domain/player.js";

export class JoinRoom {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute({ nickname, role }) {
    return this.gameApi.joinRoom({
      nickname: normalizeNickname(nickname),
      role: normalizeRole(role),
    });
  }
}
