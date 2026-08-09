export class LandingPage {
  constructor({ createRoom, documentRef = document, navigate }) {
    this.createRoom = createRoom;
    this.document = documentRef;
    this.navigate = navigate;
    this.busy = false;
  }

  mount() {
    this.document
      .getElementById("createGameForm")
      .addEventListener("submit", (event) => this.handleCreate(event));
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
}
