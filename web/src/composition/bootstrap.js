import { CreateRoom } from "../application/use-cases/create-room.js";
import { ConfirmWorld } from "../application/use-cases/confirm-world.js";
import { JoinRoom } from "../application/use-cases/join-room.js";
import { LoadRoom } from "../application/use-cases/load-room.js";
import { SubmitAction } from "../application/use-cases/submit-action.js";
import { StartGame } from "../application/use-cases/start-game.js";
import { UpdateCharacter } from "../application/use-cases/update-character.js";
import { RollRound } from "../application/use-cases/roll-round.js";
import { FetchGameApi } from "../adapters/api/fetch-game-api.js";
import { MockGameApi } from "../adapters/api/mock-game-api.js";
import { GamePage } from "../ui/pages/game-page.js";

const config = globalThis.CO_STORY_CONFIG ?? { apiMode: "mock", apiBasePath: "/api/v1" };
const gameApi = config.apiMode === "http"
  ? new FetchGameApi({ basePath: config.apiBasePath })
  : new MockGameApi();
const page = new GamePage({
  loadRoom: new LoadRoom(gameApi),
  createRoom: new CreateRoom(gameApi),
  joinRoom: new JoinRoom(gameApi),
  confirmWorld: new ConfirmWorld(gameApi),
  startGame: new StartGame(gameApi),
  updateCharacter: new UpdateCharacter(gameApi),
  submitAction: new SubmitAction(gameApi),
  rollRound: new RollRound(gameApi),
  connectionLabel: config.apiMode === "http" ? "本機 FastAPI 模式" : "本機 Mock API 模式",
  persistenceLabel: config.apiMode === "http"
    ? "本機原型 · 遊戲資料由 FastAPI memory repository 管理"
    : "本機原型 · 遊戲資料由 Mock API 保存在記憶體",
});

page.mount();
