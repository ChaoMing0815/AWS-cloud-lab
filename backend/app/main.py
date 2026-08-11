import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.postgres_room_repository import PostgresRoomRepository
from app.adapters.memory_idempotency_store import MemoryIdempotencyStore
from app.adapters.mock_storyteller import MockStoryteller
from app.adapters.session_security import HmacSessionTokenFactory
from app.adapters.system_clock import SystemClock
from app.adapters.secure_dice_roller import SecureDiceRoller
from app.api.routes import create_api_router
from app.application.room_service import RoomService
from app.domain.errors import DomainError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


def create_app(dice_roller=None, room_repository=None, storyteller=None, clock=None) -> FastAPI:
    application = FastAPI(title="共演計劃 API", version="0.1.0")
    if room_repository is None:
        database_url = os.environ.get("DATABASE_URL")
        room_repository = (
            PostgresRoomRepository(database_url)
            if database_url
            else MemoryRoomRepository()
        )
    service = RoomService(
        room_repository,
        storyteller or MockStoryteller(),
        MemoryIdempotencyStore(),
        HmacSessionTokenFactory(),
        dice_roller or SecureDiceRoller(),
        clock or SystemClock(),
    )
    application.state.room_service = service

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"error": {"code": error.code, "message": error.message}},
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, error: StarletteHTTPException):
        if error.status_code == 404 and not request.url.path.startswith("/api/"):
            return FileResponse(WEB_ROOT / "404.html", status_code=404)
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail},
            headers=error.headers,
        )

    secure_cookies = os.environ.get("CO_STORY_COOKIE_SECURE", "false").lower() == "true"
    application.include_router(create_api_router(service, secure_cookies=secure_cookies))

    @application.get("/demo", include_in_schema=False)
    async def demo_app_shell() -> FileResponse:
        return FileResponse(WEB_ROOT / "index.html")

    @application.get("/host/setup", include_in_schema=False)
    async def host_setup_app_shell() -> FileResponse:
        return FileResponse(WEB_ROOT / "index.html")

    @application.get("/room/{room_code}/lobby", include_in_schema=False)
    async def lobby_app_shell(room_code: str) -> FileResponse:
        return FileResponse(WEB_ROOT / "index.html")

    @application.get("/room/{room_code}/play", include_in_schema=False)
    async def play_app_shell(room_code: str) -> FileResponse:
        return FileResponse(WEB_ROOT / "index.html")

    @application.get("/room/{room_code}/ending", include_in_schema=False)
    async def ending_app_shell(room_code: str) -> FileResponse:
        return FileResponse(WEB_ROOT / "index.html")

    application.mount("/", StaticFiles(directory=WEB_ROOT, html=True), name="web")
    return application


app = create_app()
