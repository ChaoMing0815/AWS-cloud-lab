export class LandingPage {
  constructor({ createRoom, joinRoomByCode, documentRef = document, navigate }) {
    this.createRoom = createRoom;
    this.joinRoomByCode = joinRoomByCode;
    this.document = documentRef;
    this.navigate = navigate;
    this.busy = false;
  }

  mount() {
    this.document
      .getElementById("createGameForm")
      .addEventListener("submit", (event) => this.handleCreate(event));
    this.document
      .getElementById("joinGameForm")
      .addEventListener("submit", (event) => this.handleJoin(event));
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
      error.textContent = caught?.message ?? "加入房間失敗，請稍後再試。";
      error.hidden = false;
    } finally {
      this.busy = false;
      button.disabled = false;
    }
  }
}
