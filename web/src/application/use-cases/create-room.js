export class CreateRoom {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute() {
    return this.gameApi.createRoom();
  }
}
