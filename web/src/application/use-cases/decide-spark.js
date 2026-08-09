import { DomainError } from "../../domain/domain-error.js";

export class DecideSpark {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute({ decision }) {
    if (!["USE", "DECLINE"].includes(decision)) {
      throw new DomainError("INVALID_SPARK_DECISION", "星火決策必須是使用或保留。");
    }
    return this.gameApi.decideSpark({ decision });
  }
}
