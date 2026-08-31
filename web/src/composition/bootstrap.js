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
import { GenerateWorld } from "../application/use-cases/generate-world.js";
import { FetchGameApi } from "../adapters/api/fetch-game-api.js";
import { FetchSupportApi } from "../adapters/api/fetch-support-api.js";
import { MockGameApi } from "../adapters/api/mock-game-api.js";
import {
  CreateSupportReportDraft,
  LookupSupportRule,
} from "../application/use-cases/ask-support-agent.js";
import { GamePage } from "../ui/pages/game-page.js";
import { LandingPage } from "../ui/pages/landing-page.js";
import { SupportPage } from "../ui/pages/support-page.js";

function showServerRequiredNoticeForFileProtocol() {
  const serverRequiredNotice = document.getElementById("serverRequiredNotice");
  if (globalThis.location.protocol === "file:") {
    serverRequiredNotice.hidden = false;
  }
}

globalThis.addEventListener("popstate", () => globalThis.location.reload());

const SURFACE_IDS = ["landingPage", "gamePage", "rulesPage", "supportPage"];

function showLoading() {
  SURFACE_IDS.forEach((id) => { document.getElementById(id).hidden = true; });
  document.getElementById("appLoadingStatus").hidden = false;
}

function showSurface(surfaceId) {
  SURFACE_IDS.forEach((id) => { document.getElementById(id).hidden = id !== surfaceId; });
  document.getElementById("appLoadingStatus").hidden = true;
}

async function mountGamePage({ forceMock = false } = {}) {
  showLoading();
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
    generateWorld: new GenerateWorld(gameApi),
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
    connectionLabel: apiMode === "http" ? "AWS 公開試玩" : "教學 Demo · 不保存進度",
    persistenceLabel: apiMode === "http"
      ? "AWS Tier 0 · 遊戲資料儲存於 private PostgreSQL"
      : "教學 Demo · 資料只存在本頁記憶體，重新進入即重設",
    navigate: forceMock ? null : (route) => {
      if (globalThis.location.pathname !== route) {
        globalThis.history.replaceState({}, "", route);
      }
    },
  });

  await page.mount();
  showSurface("gamePage");
}

async function mountSupportPage() {
  showLoading();
  const config = globalThis.CO_STORY_CONFIG ?? { apiBasePath: "/api/v1" };
  const gameApi = new FetchGameApi({ basePath: config.apiBasePath });
  const loadRoom = new LoadRoom(gameApi);
  let playerSession = null;
  try {
    const room = await loadRoom.execute();
    playerSession = room?.session ?? null;
  } catch {
    playerSession = null;
  }
  const canDraftReport = playerSession?.principalType === "player"
    && typeof playerSession?.csrfToken === "string"
    && playerSession.csrfToken.trim().length > 0;
  const supportApi = new FetchSupportApi({
    basePath: config.apiBasePath,
    playerSessionProvider: async () => playerSession,
  });
  const page = new SupportPage({
    lookupSupportRule: new LookupSupportRule(supportApi),
    createSupportReportDraft: new CreateSupportReportDraft(supportApi),
    canDraftReport,
  });
  page.mount();
  showSurface("supportPage");
}

async function bootstrap() {
  const path = globalThis.location?.pathname ?? "/";
  const formalRoomPath = /^\/room\/[A-HJ-NP-Z2-9]{6}/;
  const formalGameSuffixes = ["/lobby", "/play", "/ending"];
  if (path === "/demo") await mountGamePage({ forceMock: true });
  else if (path === "/host/setup") await mountGamePage();
  else if (path === "/support") await mountSupportPage();
  else if (path === "/rules") showSurface("rulesPage");
  else if (formalRoomPath.test(path) && formalGameSuffixes.some((suffix) => path.endsWith(suffix))) {
    await mountGamePage();
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
        void mountGamePage();
      },
    });
    landing.mount();
    showSurface("landingPage");
  }
}

showServerRequiredNoticeForFileProtocol();
void bootstrap();
