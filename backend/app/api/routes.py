from fastapi import APIRouter, Cookie, Header, Response, status
from fastapi.responses import JSONResponse

from app.api.schemas import (
    ConfirmWorldRequest,
    CreateRoomRequest,
    DeleteRoomRequest,
    FallbackRoundRequest,
    FinishRoomRequest,
    GenerateWorldRequest,
    IssueTransferCodeRequest,
    JoinRoomRequest,
    JoinRoomByCodeRequest,
    ResolveRoundRequest,
    ReassignPlayerRequest,
    RollRoundRequest,
    SparkDecisionRequest,
    StartGameRequest,
    SubmitActionRequest,
    UpdateCharacterRequest,
)
from app.api.serialization import room_response
from app.application.room_service import RoomService
from app.domain.errors import DomainError

LOCAL_ROOM_COOKIE = "co_story_local_room"
HOST_SESSION_COOKIE = "co_story_host"
PLAYER_SESSION_COOKIE = "co_story_player"


def create_api_router(service: RoomService, *, secure_cookies: bool = False) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "co-story-api", "storyteller": "mock"}

    @router.get("/live")
    def live() -> dict:
        return {"status": "ok", "service": "co-story-api"}

    @router.get("/ready")
    def ready():
        probe = getattr(service.repository, "is_ready", None)
        try:
            is_ready = True if probe is None else bool(probe())
        except Exception:
            is_ready = False
        if not is_ready:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "unavailable", "service": "co-story-api"},
            )
        return {"status": "ok", "service": "co-story-api"}

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
        session = service.session_context(room, host_token, player_token)
        if session["principalType"] == "anonymous":
            raise DomainError("SESSION_NOT_FOUND", "目前的遊戲工作階段已失效。", 401)
        _set_local_room_cookie(response, room.id, secure=secure_cookies)
        return room_response(room, session)

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

    @router.post("/rooms/{room_id}/rounds/{round_number}:fallback")
    def fallback_round(
        room_id: str,
        round_number: int,
        request: FallbackRoundRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
    ) -> dict:
        room = service.fallback_round(
            room_id,
            round_number,
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
        _set_local_room_cookie(response, room.id, secure=secure_cookies)
        _set_session_cookie(response, HOST_SESSION_COOKIE, host_token, secure=secure_cookies)
        _set_session_cookie(response, PLAYER_SESSION_COOKIE, player_token, secure=secure_cookies)
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
        _set_local_room_cookie(response, room.id, secure=secure_cookies)
        _set_session_cookie(response, PLAYER_SESSION_COOKIE, player_token, secure=secure_cookies)
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
        _set_local_room_cookie(response, room.id, secure=secure_cookies)
        _set_session_cookie(response, PLAYER_SESSION_COOKIE, player_token, secure=secure_cookies)
        return room_response(room, service.session_context(room, host_token, player_token))

    @router.post("/rooms/{room_id}/players/{player_id}/transfer-codes")
    def issue_transfer_code(
        room_id: str,
        player_id: str,
        request: IssueTransferCodeRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
    ) -> dict:
        room, transfer_code = service.issue_transfer_code(
            room_id,
            player_id,
            request.room_version,
            host_token or "",
            csrf_token or "",
            _required_idempotency_key(idempotency_key),
        )
        metadata = next(player for player in room.players if player.id == player_id).transfer_code
        if metadata is None:
            raise RuntimeError("Transfer code was not issued")
        return {
            "playerId": player_id,
            "transferCode": transfer_code,
            "expiresAt": metadata.expires_at.isoformat(),
            "transfersHostPlayer": room.host_player_id == player_id,
            "hostSessionTransferred": False,
        }

    @router.post("/rooms/{room_id}/players/{player_id}:reassign")
    def reassign_player(
        room_id: str,
        player_id: str,
        request: ReassignPlayerRequest,
        response: Response,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict:
        room, player_token, _ = service.redeem_transfer_code(
            room_id,
            player_id,
            request.transfer_code,
            request.room_version,
            _required_idempotency_key(idempotency_key),
        )
        _set_local_room_cookie(response, room.id, secure=secure_cookies)
        _set_session_cookie(response, PLAYER_SESSION_COOKIE, player_token, secure=secure_cookies)
        return room_response(room, service.session_context(room, None, player_token))

    @router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_room(
        room_id: str,
        request: DeleteRoomRequest,
        response: Response,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
    ) -> None:
        service.delete_room(
            room_id,
            request.room_version,
            host_token or "",
            csrf_token or "",
            _required_idempotency_key(idempotency_key),
        )
        for cookie in (LOCAL_ROOM_COOKIE, HOST_SESSION_COOKIE, PLAYER_SESSION_COOKIE):
            response.delete_cookie(
                cookie,
                path="/",
                httponly=True,
                samesite="lax",
                secure=secure_cookies,
            )

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

    @router.post("/rooms/{room_id}/world:generate")
    def generate_world(
        room_id: str,
        request: GenerateWorldRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
        host_token: str | None = Cookie(default=None, alias=HOST_SESSION_COOKIE),
        player_token: str | None = Cookie(default=None, alias=PLAYER_SESSION_COOKIE),
    ) -> dict:
        room = service.generate_world(
            room_id,
            request.keywords,
            request.tone,
            request.custom_tone,
            request.supplemental_request,
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


def _set_local_room_cookie(response: Response, room_id: str, *, secure: bool) -> None:
    response.set_cookie(
        key=LOCAL_ROOM_COOKIE,
        value=room_id,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=60 * 60 * 24 * 7,
    )


def _set_session_cookie(response: Response, name: str, token: str, *, secure: bool) -> None:
    response.set_cookie(
        key=name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=60 * 60 * 24 * 7,
    )


def _required_idempotency_key(value: str | None) -> str:
    from app.domain.errors import DomainError

    if not value:
        raise DomainError("IDEMPOTENCY_KEY_REQUIRED", "此操作需要 Idempotency-Key。", 400)
    return value
