import { DomainError } from "../../domain/domain-error.js";


export class FinishGame {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute({ decision }) {
    if (!["FINISH_NOW", "CONTINUE"].includes(decision)) {
      throw new DomainError("INVALID_COMPLETION_DECISION", "結局選擇必須是立即結束或繼續。");
    }
    return this.gameApi.finishGame({ decision });
  }
}
