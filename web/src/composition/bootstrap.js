import { CreateRoom } from "../application/use-cases/create-room.js";
import { ConfirmWorld } from "../application/use-cases/confirm-world.js";
import { JoinRoom } from "../application/use-cases/join-room.js";
import { JoinRoomByCode } from "../application/use-cases/join-room-by-code.js";
import { LoadRoom } from "../application/use-cases/load-room.js";
import { LoadCurrentSession } from "../application/use-cases/load-current-session.js";
import { SubmitAction } from "../application/use-cases/submit-action.js";
import { StartGame } from "../application/use-cases/start-game.js";
import { UpdateCharacter } from "../application/use-cases/update-character.js";
import { RollRound } from "../application/use-cases/roll-round.js";
import { DecideSpark } from "../application/use-cases/decide-spark.js";
import { ResolveRound } from "../application/use-cases/resolve-round.js";
import { FallbackRound } from "../application/use-cases/fallback-round.js";
import { FinishGame } from "../application/use-cases/finish-game.js";
import { DeleteRoom } from "../application/use-cases/delete-room.js";
import { FetchGameApi } from "../adapters/api/fetch-game-api.js";
import { MockGameApi } from "../adapters/api/mock-game-api.js";
import { GamePage } from "../ui/pages/game-page.js";
import { LandingPage } from "../ui/pages/landing-page.js";

function mountGamePage({ forceMock = false } = {}) {
  const config = globalThis.CO_STORY_CONFIG ?? { apiMode: "mock", apiBasePath: "/api/v1" };
  const apiMode = forceMock ? "mock" : config.apiMode;
  const gameApi = apiMode === "http"
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
    decideSpark: new DecideSpark(gameApi),
    resolveRound: new ResolveRound(gameApi),
    fallbackRound: new FallbackRound(gameApi),
    finishGame: new FinishGame(gameApi),
    deleteRoom: new DeleteRoom(gameApi),
    apiMode,
    connectionLabel: apiMode === "http" ? "本機 FastAPI 模式" : "教學 Demo · 不保存進度",
    persistenceLabel: apiMode === "http"
      ? "本機原型 · 遊戲資料由 FastAPI memory repository 管理"
      : "教學 Demo · 資料只存在本頁記憶體，重新進入即重設",
    navigate: forceMock ? null : (route) => {
      if (globalThis.location.pathname !== route) {
        globalThis.history.replaceState({}, "", route);
      }
    },
  });

  document.getElementById("landingPage").hidden = true;
  document.getElementById("gamePage").hidden = false;
  page.mount();
}

const path = globalThis.location?.pathname ?? "/";
const formalRoomPath = /^\/room\/[A-HJ-NP-Z2-9]{6}/;
const formalGameSuffixes = ["/lobby", "/play", "/ending"];
if (path === "/demo") mountGamePage({ forceMock: true });
else if (path === "/host/setup") mountGamePage();
else if (formalRoomPath.test(path) && formalGameSuffixes.some((suffix) => path.endsWith(suffix))) {
  mountGamePage();
}
else if (path === "/") {
  const config = globalThis.CO_STORY_CONFIG ?? { apiBasePath: "/api/v1" };
  const gameApi = new FetchGameApi({ basePath: config.apiBasePath });
  const landing = new LandingPage({
    createRoom: new CreateRoom(gameApi),
    joinRoomByCode: new JoinRoomByCode(gameApi),
    loadCurrentSession: new LoadCurrentSession(gameApi),
    navigate(route) {
      globalThis.history.pushState({}, "", route);
      mountGamePage();
    },
  });
  landing.mount();
}
