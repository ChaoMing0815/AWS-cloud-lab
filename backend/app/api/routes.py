from fastapi import APIRouter, Cookie, Header, Response, status

from app.api.schemas import JoinRoomRequest, SubmitActionRequest
from app.api.serialization import room_response
from app.application.room_service import RoomService

LOCAL_ROOM_COOKIE = "co_story_local_room"
HOST_SESSION_COOKIE = "co_story_host"
PLAYER_SESSION_COOKIE = "co_story_player"


def create_api_router(service: RoomService) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "co-story-api", "storyteller": "mock"}

    @router.get("/rooms/current")
    def current_room(
        response: Response,
        room_id: str | None = Cookie(default=None, alias=LOCAL_ROOM_COOKIE),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
    ) -> dict:
        room = service.load_current(room_id)
        _set_local_room_cookie(response, room.id)
        return room_response(room, service.session_context(room, host_token, player_token))

    @router.post("/rooms", status_code=status.HTTP_201_CREATED)
    def create_room(
        response: Response,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict:
        room, host_token = service.create_room(_required_idempotency_key(idempotency_key))
        _set_local_room_cookie(response, room.id)
        _set_session_cookie(response, HOST_SESSION_COOKIE, host_token)
        return room_response(room, service.session_context(room, host_token, None))

    @router.post("/rooms/{room_id}/players", status_code=status.HTTP_201_CREATED)
    def join_room(
        room_id: str,
        request: JoinRoomRequest,
        response: Response,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
    ) -> dict:
        room, player_token = service.join_room(
            room_id,
            request.nickname,
            request.role,
            request.room_version,
            _required_idempotency_key(idempotency_key),
        )
        _set_local_room_cookie(response, room.id)
        _set_session_cookie(response, PLAYER_SESSION_COOKIE, player_token)
        return room_response(room, service.session_context(room, host_token, player_token))

    @router.put("/rooms/{room_id}/rounds/{round_number}/action")
    def submit_action(
        room_id: str,
        round_number: int,
        request: SubmitActionRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
    ) -> dict:
        room = service.submit_action(
            room_id,
            round_number,
            request.text,
            request.room_version,
            player_token or "",
            csrf_token or "",
            _required_idempotency_key(idempotency_key),
        )
        return room_response(room, service.session_context(room, host_token, player_token))

    return router


def _set_local_room_cookie(response: Response, room_id: str) -> None:
    response.set_cookie(
        key=LOCAL_ROOM_COOKIE,
        value=room_id,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24,
    )


def _set_session_cookie(response: Response, name: str, token: str) -> None:
    response.set_cookie(
        key=name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24,
    )


def _required_idempotency_key(value: str | None) -> str:
    from app.domain.errors import DomainError

    if not value:
        raise DomainError("IDEMPOTENCY_KEY_REQUIRED", "此操作需要 Idempotency-Key。", 400)
    return value
