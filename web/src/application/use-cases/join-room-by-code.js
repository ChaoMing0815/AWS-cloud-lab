import { DomainError } from "../../domain/domain-error.js";

const ROOM_CODE_PATTERN = /^[A-HJ-NP-Z2-9]{6}$/;

export class JoinRoomByCode {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute({ roomCode, nickname }) {
    const normalizedRoomCode = String(roomCode ?? "").trim().toUpperCase();
    const normalizedNickname = String(nickname ?? "").trim();
    if (!ROOM_CODE_PATTERN.test(normalizedRoomCode)) {
      throw new DomainError("ROOM_CODE_INVALID", "房間代碼必須是六碼英數字。");
    }
    if (!normalizedNickname || normalizedNickname.length > 12) {
      throw new DomainError("INVALID_NICKNAME", "暱稱必須是 1–12 個字元。");
    }
    return this.gameApi.joinRoomByCode({
      roomCode: normalizedRoomCode,
      nickname: normalizedNickname,
    });
  }
}
