import json
import logging
import os
from time import perf_counter
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.postgres_room_repository import PostgresRoomRepository
from app.adapters.postgres_story_resolution_store import PostgresStoryResolutionStore
from app.adapters.memory_idempotency_store import MemoryIdempotencyStore
from app.adapters.mock_storyteller import MockStoryteller
from app.adapters.session_security import HmacSessionTokenFactory
from app.adapters.safe_application_file_logging import (
    configure_safe_application_file_logging,
)
from app.adapters.system_clock import SystemClock
from app.adapters.secure_dice_roller import SecureDiceRoller
from app.api.routes import create_api_router
from app.application.room_service import RoomService
from app.application.story_resolution import StoryResolutionProducer
from app.domain.errors import DomainError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"
REQUEST_LOGGER = logging.getLogger("co_story.request")


def _comma_separated_setting(name: str) -> tuple[str, ...]:
    return tuple(
        value.strip()
        for value in os.environ.get(name, "").split(",")
        if value.strip()
    )


def _production_configuration_is_valid() -> bool:
    if os.environ.get("CO_STORY_ENV", "").lower() != "production":
        return False

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL")
    if os.environ.get("CO_STORY_COOKIE_SECURE", "").lower() != "true":
        raise RuntimeError("CO_STORY_COOKIE_SECURE")
    if not _comma_separated_setting("CO_STORY_ALLOWED_HOSTS"):
        raise RuntimeError("CO_STORY_ALLOWED_HOSTS")
    if not _comma_separated_setting("CO_STORY_ALLOWED_ORIGINS"):
        raise RuntimeError("CO_STORY_ALLOWED_ORIGINS")

    query = parse_qs(urlsplit(database_url).query, keep_blank_values=True)
    sslmode = query.get("sslmode")
    sslrootcert = query.get("sslrootcert")
    if sslmode != ["verify-full"] or sslrootcert is None or not sslrootcert[0].strip():
        raise RuntimeError("DATABASE_URL")
    return True


def _required_setting(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(name)
    return value


def _production_bedrock_storyteller():
    region = _required_setting("CO_STORY_AWS_REGION")
    model_id = _required_setting("CO_STORY_BEDROCK_MODEL_ID")
    guardrail_id = _required_setting("CO_STORY_BEDROCK_GUARDRAIL_ID")
    guardrail_version = _required_setting("CO_STORY_BEDROCK_GUARDRAIL_VERSION")
    raw_max_tokens = _required_setting("CO_STORY_BEDROCK_MAX_TOKENS")
    try:
        max_tokens = int(raw_max_tokens)
    except ValueError:
        raise RuntimeError("CO_STORY_BEDROCK_MAX_TOKENS") from None
    if not 1 <= max_tokens <= 1200:
        raise RuntimeError("CO_STORY_BEDROCK_MAX_TOKENS")

    import boto3
    from botocore.config import Config

    from app.adapters.bedrock_storyteller import BedrockStoryteller

    client = boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(
            read_timeout=30,
            connect_timeout=5,
            retries={"max_attempts": 0},
        ),
    )
    return BedrockStoryteller(
        client=client,
        model_id=model_id,
        guardrail_id=guardrail_id,
        guardrail_version=guardrail_version,
        max_tokens=max_tokens,
    )


def create_app(
    dice_roller=None,
    room_repository=None,
    storyteller=None,
    clock=None,
    story_resolution_producer=None,
) -> FastAPI:
    configure_safe_application_file_logging(
        os.environ.get("CO_STORY_APPLICATION_LOG_PATH")
    )
    production = _production_configuration_is_valid()
    if storyteller is None:
        storyteller = _production_bedrock_storyteller() if production else MockStoryteller()
    application = FastAPI(title="共演計劃 API", version="0.1.0")
    allowed_hosts = _comma_separated_setting("CO_STORY_ALLOWED_HOSTS")
    allowed_origins = _comma_separated_setting("CO_STORY_ALLOWED_ORIGINS")
    if production:
        application.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    database_url = os.environ.get("DATABASE_URL")
    repository_from_database_url = room_repository is None and bool(database_url)
    if room_repository is None:
        room_repository = (
            PostgresRoomRepository(database_url)
            if database_url
            else MemoryRoomRepository()
        )
    resolved_clock = clock or SystemClock()
    if story_resolution_producer is None and repository_from_database_url:
        story_resolution_producer = StoryResolutionProducer(
            PostgresStoryResolutionStore(database_url, clock=resolved_clock)
        )
    service = RoomService(
        room_repository,
        storyteller,
        MemoryIdempotencyStore(),
        HmacSessionTokenFactory(),
        dice_roller or SecureDiceRoller(),
        resolved_clock,
        seed_demo_room=not production,
        story_resolution_producer=story_resolution_producer,
    )
    application.state.room_service = service

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        request_id = uuid4().hex
        started_at = perf_counter()
        unsafe_api_request = request.url.path.startswith("/api/") and request.method in {
            "POST", "PUT", "PATCH", "DELETE",
        }
        if production and unsafe_api_request and request.headers.get("origin") not in allowed_origins:
            response = JSONResponse(status_code=403, content={"detail": "Forbidden"})
        else:
            response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = request_id
        REQUEST_LOGGER.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "latency_ms": int((perf_counter() - started_at) * 1000),
                },
                separators=(",", ":"),
            )
        )
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

    @application.get("/rules", include_in_schema=False)
    async def rules_app_shell() -> FileResponse:
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
