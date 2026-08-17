export class DeleteRoom {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute() {
    return this.gameApi.deleteRoom();
  }
}
