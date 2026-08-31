from __future__ import annotations

import hmac
from datetime import timedelta
from threading import Lock

from fastapi import APIRouter, Cookie, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from app.api.routes import (
    HOST_SESSION_COOKIE,
    LOCAL_ROOM_COOKIE,
    PLAYER_SESSION_COOKIE,
)
from app.api.support_schemas import DraftReportRequest, RuleLookupRequest
from app.api.support_serialization import report_draft_response, rule_answer_response
from app.application.room_service import RoomService
from app.application.support_agent import SupportAgent, SupportAgentRejected
from app.domain.support_agent import SupportReportConflict


_ERRORS = {
    "SESSION_NOT_FOUND": (401, "目前的遊戲工作階段已失效。"),
    "PLAYER_SESSION_REQUIRED": (401, "需要有效的玩家工作階段。"),
    "CSRF_FAILED": (403, "CSRF 驗證失敗。"),
    "SUPPORT_REPORT_CONFLICT": (409, "問題草稿狀態衝突，請重新整理後再試。"),
    "REQUEST_VALIDATION_FAILED": (422, "請檢查輸入內容。"),
    "SUPPORT_RATE_LIMITED": (429, "操作過於頻繁，請稍後再試。"),
    "SUPPORT_UNAVAILABLE": (500, "客服暫時無法使用，請稍後再試。"),
}


def _error(code: str) -> JSONResponse:
    status_code, message = _ERRORS[code]
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


class FixedWindowRateLimiter:
    def __init__(self, *, limit: int, window: timedelta, clock) -> None:
        if limit < 1 or window.total_seconds() <= 0:
            raise ValueError("rate limiter boundaries must be positive")
        self._limit = limit
        self._window = window
        self._clock = clock
        self._entries: dict[str, tuple[object, int]] = {}
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = self._clock.now()
        with self._lock:
            started_at, count = self._entries.get(key, (now, 0))
            if now - started_at >= self._window:
                started_at, count = now, 0
            if count >= self._limit:
                return False
            self._entries[key] = (started_at, count + 1)
            return True


async def _bounded_json(request: Request, model: type[BaseModel], maximum: int):
    content_type = request.headers.get("content-type", "").partition(";")[0].strip().lower()
    if content_type != "application/json":
        raise ValueError("invalid content type")
    raw_length = request.headers.get("content-length")
    if raw_length is not None:
        try:
            if int(raw_length) < 0 or int(raw_length) > maximum:
                raise ValueError("request body is too large")
        except ValueError as error:
            raise ValueError("invalid content length") from error
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > maximum:
            raise ValueError("request body is too large")
    if not body:
        raise ValueError("request body is empty")
    try:
        return model.model_validate_json(bytes(body))
    except ValidationError as error:
        raise ValueError("invalid support request") from error


def create_support_router(
    support_agent: SupportAgent,
    room_service: RoomService,
    *,
    rule_limiter: FixedWindowRateLimiter,
    report_limiter: FixedWindowRateLimiter,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/support")

    @router.post("/rules:lookup")
    async def lookup_rules(request: Request):
        try:
            payload = await _bounded_json(request, RuleLookupRequest, 1024)
        except ValueError:
            return _error("REQUEST_VALIDATION_FAILED")
        source = request.client.host if request.client is not None else "unknown"
        if not rule_limiter.allow(source):
            return _error("SUPPORT_RATE_LIMITED")
        try:
            return rule_answer_response(support_agent.lookup_game_rules(payload.message))
        except SupportAgentRejected:
            return _error("REQUEST_VALIDATION_FAILED")
        except Exception:
            return _error("SUPPORT_UNAVAILABLE")

    @router.post("/reports:draft", status_code=201)
    async def draft_report(
        request: Request,
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        room_id: str | None = Cookie(default=None, alias=LOCAL_ROOM_COOKIE),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
    ):
        try:
            payload = await _bounded_json(request, DraftReportRequest, 4096)
        except ValueError:
            return _error("REQUEST_VALIDATION_FAILED")
        if not room_id:
            return _error("SESSION_NOT_FOUND")
        room = room_service.repository.get(room_id)
        if room is None:
            return _error("SESSION_NOT_FOUND")
        session = room_service.session_context(room, host_token, player_token)
        if session["principalType"] == "anonymous":
            return _error("SESSION_NOT_FOUND")
        if session["principalType"] != "player" or not session["playerId"]:
            return _error("PLAYER_SESSION_REQUIRED")
        expected_csrf = session["csrfToken"]
        if (
            not csrf_token
            or not expected_csrf
            or not hmac.compare_digest(expected_csrf, csrf_token)
        ):
            return _error("CSRF_FAILED")
        reporter_identity = f"{room.id}:{session['playerId']}"
        if not report_limiter.allow(reporter_identity):
            return _error("SUPPORT_RATE_LIMITED")
        try:
            draft = support_agent.draft_problem_report(
                payload.description,
                reporter_identity=reporter_identity,
            )
            return report_draft_response(draft)
        except SupportReportConflict:
            return _error("SUPPORT_REPORT_CONFLICT")
        except SupportAgentRejected:
            return _error("REQUEST_VALIDATION_FAILED")
        except Exception:
            return _error("SUPPORT_UNAVAILABLE")

    return router
