export class ResolveRound {
  constructor(gameApi) {
    this.gameApi = gameApi;
  }

  execute({ skipPendingSpark = false } = {}) {
    return this.gameApi.resolveRound({ skipPendingSpark: Boolean(skipPendingSpark) });
  }
}
