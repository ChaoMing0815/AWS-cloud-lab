function joinErrorMessage(error) {
  if (error?.status === 409 && error?.code === "ROOM_NOT_JOINABLE") {
    return "房主尚未開放世界，請稍後再試。";
  }
  return error?.message ?? "加入房間失敗，請稍後再試。";
}

export class LandingPage {
  constructor({ createRoom, joinRoomByCode, loadCurrentSession, documentRef = document, navigate }) {
    this.createRoom = createRoom;
    this.joinRoomByCode = joinRoomByCode;
    this.loadCurrentSession = loadCurrentSession;
    this.document = documentRef;
    this.navigate = navigate;
    this.busy = false;
    this.continueRoute = null;
  }

  mount() {
    this.document
      .getElementById("createGameForm")
      .addEventListener("submit", (event) => this.handleCreate(event));
    this.document
      .getElementById("joinGameForm")
      .addEventListener("submit", (event) => this.handleJoin(event));
    this.document
      .getElementById("continueGameButton")
      .addEventListener("click", () => this.handleContinue());
    this.restoreCurrentSession();
  }

  async handleCreate(event) {
    event.preventDefault();
    if (this.busy) return;
    const button = this.document.getElementById("createGameButton");
    const error = this.document.getElementById("createGameError");
    this.busy = true;
    button.disabled = true;
    error.hidden = true;
    error.textContent = "";
    try {
      await this.createRoom.execute({
        nickname: this.document.getElementById("hostNickname").value,
      });
      this.navigate("/host/setup");
    } catch (caught) {
      error.textContent = caught?.message ?? "建立房間失敗，請稍後再試。";
      error.hidden = false;
    } finally {
      this.busy = false;
      button.disabled = false;
    }
  }

  async handleJoin(event) {
    event.preventDefault();
    if (this.busy) return;
    const button = this.document.getElementById("joinGameButton");
    const error = this.document.getElementById("joinGameError");
    this.busy = true;
    button.disabled = true;
    error.hidden = true;
    error.textContent = "";
    try {
      const room = await this.joinRoomByCode.execute({
        roomCode: this.document.getElementById("joinRoomCode").value,
        nickname: this.document.getElementById("joinNickname").value,
      });
      this.navigate(`/room/${room.roomCode}/lobby`);
    } catch (caught) {
      error.textContent = joinErrorMessage(caught);
      error.hidden = false;
    } finally {
      this.busy = false;
      button.disabled = false;
    }
  }

  async restoreCurrentSession() {
    const panel = this.document.getElementById("continueGamePanel");
    const summary = this.document.getElementById("currentGameSummary");
    const notice = this.document.getElementById("sessionNotice");
    panel.hidden = true;
    notice.hidden = true;
    notice.textContent = "";
    this.continueRoute = null;
    try {
      const session = await this.loadCurrentSession.execute();
      if (!session.authenticated || !session.continueRoute) return;
      this.continueRoute = session.continueRoute;
      summary.textContent = `房間 ${session.room.roomCode} · ${session.room.status}`;
      panel.hidden = false;
    } catch (caught) {
      notice.textContent = caught?.message ?? "無法確認目前遊戲，請稍後再試。";
      notice.hidden = false;
    }
  }

  handleContinue() {
    if (this.continueRoute) this.navigate(this.continueRoute);
  }
}
