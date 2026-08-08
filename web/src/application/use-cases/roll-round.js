export class RollRound {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute() {
    return this.gameApi.rollRound();
  }
}
