from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.memory_idempotency_store import MemoryIdempotencyStore
from app.adapters.mock_storyteller import MockStoryteller
from app.adapters.session_security import HmacSessionTokenFactory
from app.api.routes import create_api_router
from app.application.room_service import RoomService
from app.domain.errors import DomainError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


def create_app() -> FastAPI:
    application = FastAPI(title="共演計劃 API", version="0.1.0")
    service = RoomService(
        MemoryRoomRepository(),
        MockStoryteller(),
        MemoryIdempotencyStore(),
        HmacSessionTokenFactory(),
    )

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

    application.include_router(create_api_router(service))
    application.mount("/", StaticFiles(directory=WEB_ROOT, html=True), name="web")
    return application


app = create_app()
