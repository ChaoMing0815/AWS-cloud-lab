import { DomainError } from "../../domain/domain-error.js";

export class CreateRoom {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute({ nickname }) {
    const normalizedNickname = String(nickname ?? "").trim();
    if (!normalizedNickname || normalizedNickname.length > 12) {
      throw new DomainError("INVALID_NICKNAME", "暱稱必須是 1–12 個字元。");
    }
    return this.gameApi.createRoom({ nickname: normalizedNickname });
  }
}
