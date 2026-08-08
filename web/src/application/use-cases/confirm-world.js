import { DomainError } from "../../domain/domain-error.js";

export class ConfirmWorld {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  async execute(command) {
    const world = Object.fromEntries(
      Object.entries(command).map(([key, value]) => [key, typeof value === "string" ? value.trim() : value]),
    );
    if (![4, 6, 8].includes(world.maxRounds)) {
      throw new DomainError("INVALID_ROUND_LIMIT", "回合上限必須是 4、6 或 8。", 422);
    }
    if (world.tone === "custom" && !world.customTone) {
      throw new DomainError("INVALID_CUSTOM_TONE", "請填寫自訂故事調性。", 422);
    }
    return this.gameApi.confirmWorld(world);
  }
}
