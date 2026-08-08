export class LoadRoom {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute() {
    return this.gameApi.loadRoom();
  }
}
