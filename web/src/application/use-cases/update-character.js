import { DomainError } from "../../domain/domain-error.js";

export class UpdateCharacter {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  async execute(command) {
    const character = {
      name: command.name.trim(),
      background: command.background.trim(),
      trait: command.trait.trim(),
      weakness: command.weakness.trim(),
      courage: Number(command.courage),
      insight: Number(command.insight),
      bond: Number(command.bond),
    };
    const attributes = [character.courage, character.insight, character.bond];
    if (attributes.some((value) => !Number.isInteger(value) || value < 0 || value > 2)) {
      throw new DomainError("INVALID_ATTRIBUTE_RANGE", "每項屬性必須是 0–2 的整數。", 422);
    }
    if (attributes.reduce((total, value) => total + value, 0) !== 3) {
      throw new DomainError("INVALID_ATTRIBUTE_TOTAL", "三項屬性總和必須等於 3。", 422);
    }
    return this.gameApi.updateCharacter(character);
  }
}
