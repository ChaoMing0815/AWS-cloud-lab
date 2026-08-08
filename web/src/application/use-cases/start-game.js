export class StartGame {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  async execute() {
    return this.gameApi.startGame();
  }
}
