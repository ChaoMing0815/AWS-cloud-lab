export class FallbackRound {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute() {
    return this.gameApi.fallbackRound();
  }
}
