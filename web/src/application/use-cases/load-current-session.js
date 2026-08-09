export class LoadCurrentSession {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute() {
    return this.gameApi.loadCurrentSession();
  }
}
