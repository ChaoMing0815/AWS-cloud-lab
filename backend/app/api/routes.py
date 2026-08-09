from fastapi import APIRouter, Cookie, Header, Response, status

from app.api.schemas import (
    ConfirmWorldRequest,
    CreateRoomRequest,
    FinishRoomRequest,
    JoinRoomRequest,
    JoinRoomByCodeRequest,
    ResolveRoundRequest,
    RollRoundRequest,
    SparkDecisionRequest,
    StartGameRequest,
    SubmitActionRequest,
    UpdateCharacterRequest,
)
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

    @router.get("/session/current")
    def current_session(
        room_id: str | None = Cookie(default=None, alias=LOCAL_ROOM_COOKIE),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
    ) -> dict:
        return service.current_session_summary(room_id, host_token, player_token)

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

    @router.put("/rooms/{room_id}/rounds/{round_number}/spark")
    def decide_spark(
        room_id: str,
        round_number: int,
        request: SparkDecisionRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
    ) -> dict:
        room = service.decide_spark(
            room_id,
            round_number,
            request.decision,
            request.room_version,
            player_token or "",
            csrf_token or "",
            _required_idempotency_key(idempotency_key),
        )
        return room_response(room, service.session_context(room, host_token, player_token))

    @router.post("/rooms/{room_id}/rounds/{round_number}:resolve")
    def resolve_round(
        room_id: str,
        round_number: int,
        request: ResolveRoundRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
    ) -> dict:
        room = service.resolve_round(
            room_id,
            round_number,
            request.skip_pending_spark,
            request.room_version,
            host_token or "",
            csrf_token or "",
            _required_idempotency_key(idempotency_key),
        )
        return room_response(room, service.session_context(room, host_token, player_token))

    @router.post("/rooms", status_code=status.HTTP_201_CREATED)
    def create_room(
        request: CreateRoomRequest,
        response: Response,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict:
        room, host_token, player_token = service.create_room(
            request.nickname,
            _required_idempotency_key(idempotency_key),
        )
        _set_local_room_cookie(response, room.id)
        _set_session_cookie(response, HOST_SESSION_COOKIE, host_token)
        _set_session_cookie(response, PLAYER_SESSION_COOKIE, player_token)
        return room_response(room, service.session_context(room, host_token, player_token))

    @router.post("/rooms:join", status_code=status.HTTP_201_CREATED)
    def join_room_by_code(
        request: JoinRoomByCodeRequest,
        response: Response,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
    ) -> dict:
        room, player_token = service.join_room_by_code(
            request.room_code,
            request.nickname,
            _required_idempotency_key(idempotency_key),
        )
        _set_local_room_cookie(response, room.id)
        _set_session_cookie(response, PLAYER_SESSION_COOKIE, player_token)
        return room_response(room, service.session_context(room, host_token, player_token))

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

    @router.put("/rooms/{room_id}/world")
    def confirm_world(
        room_id: str,
        request: ConfirmWorldRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
    ) -> dict:
        room = service.confirm_world(
            room_id,
            request.model_dump(
                include={
                    "story_title",
                    "premise",
                    "objective",
                    "opening_scene",
                    "core_obstacle",
                    "tone",
                    "custom_tone",
                }
            ),
            request.max_rounds,
            request.room_version,
            host_token or "",
            csrf_token or "",
            _required_idempotency_key(idempotency_key),
        )
        return room_response(room, service.session_context(room, host_token, player_token))

    @router.post("/rooms/{room_id}:start")
    def start_game(
        room_id: str,
        request: StartGameRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
    ) -> dict:
        room = service.start_game(
            room_id,
            request.room_version,
            host_token or "",
            csrf_token or "",
            _required_idempotency_key(idempotency_key),
        )
        return room_response(room, service.session_context(room, host_token, player_token))

    @router.post("/rooms/{room_id}:finish")
    def finish_game(
        room_id: str,
        request: FinishRoomRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
    ) -> dict:
        room = service.finish_game(
            room_id,
            request.decision,
            request.room_version,
            host_token or "",
            csrf_token or "",
            _required_idempotency_key(idempotency_key),
        )
        return room_response(room, service.session_context(room, host_token, player_token))

    @router.put("/rooms/{room_id}/character")
    def update_character(
        room_id: str,
        request: UpdateCharacterRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
    ) -> dict:
        room = service.update_character(
            room_id,
            request.model_dump(exclude={"room_version"}),
            request.room_version,
            player_token or "",
            csrf_token or "",
            _required_idempotency_key(idempotency_key),
        )
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
            request.approach,
            request.room_version,
            player_token or "",
            csrf_token or "",
            _required_idempotency_key(idempotency_key),
        )
        return room_response(room, service.session_context(room, host_token, player_token))

    @router.post("/rooms/{room_id}/rounds/{round_number}:roll")
    def roll_round(
        room_id: str,
        round_number: int,
        request: RollRoundRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
    ) -> dict:
        room = service.roll_round(
            room_id,
            round_number,
            request.room_version,
            host_token or "",
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
