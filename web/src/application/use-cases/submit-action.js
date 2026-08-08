import { DomainError } from "../../domain/domain-error.js";

export class SubmitAction {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute({ text }) {
    const action = String(text ?? "").trim();
    if (action.length < 1 || action.length > 240) {
      throw new DomainError("INVALID_ACTION", "行動必須是 1–240 個字元。");
    }
    return this.gameApi.submitAction({ text: action });
  }
}
