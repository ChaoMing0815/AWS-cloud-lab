from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.adapters.memory_idempotency_store import MemoryIdempotencyStore
from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.mock_storyteller import MockStoryteller
from app.adapters.secure_dice_roller import SecureDiceRoller
from app.adapters.session_security import HmacSessionTokenFactory
from app.application.room_service import RoomService
from app.domain.errors import DomainError
from app.main import create_app


class MutableClock:
    def __init__(self, now: datetime) -> None:
        self.now_value = now

    def now(self) -> datetime:
        return self.now_value


NOW = datetime(2026, 8, 13, 15, 0, tzinfo=timezone.utc)


def _service_context() -> tuple[RoomService, MemoryRoomRepository, MutableClock]:
    clock = MutableClock(NOW)
    repository = MemoryRoomRepository()
    service = RoomService(
        repository,
        MockStoryteller(),
        MemoryIdempotencyStore(),
        HmacSessionTokenFactory(secret=b"reassign-test-secret"),
        SecureDiceRoller(),
        clock=clock,
    )
    return service, repository, clock


def _issued_grant(service: RoomService):
    room, host_token, player_token = service.create_room("房主", "create-reassign-room")
    issued_room, transfer_code = service.issue_transfer_code(
        room.id,
        room.players[0].id,
        room.version,
        host_token,
        room.host_csrf_token,
        "issue-reassign-code",
    )
    return issued_room, host_token, player_token, transfer_code


def _redeem(
    service: RoomService,
    room,
    transfer_code: str,
    *,
    key: str = "redeem-transfer-code",
    version: int | None = None,
):
    assert hasattr(service, "redeem_transfer_code"), "redeem_transfer_code 尚未建立"
    return service.redeem_transfer_code(
        room.id,
        room.players[0].id,
        transfer_code,
        room.version if version is None else version,
        key,
    )


def test_redeem_atomically_consumes_grant_rotates_player_session_and_preserves_host_metadata() -> None:
    service, repository, clock = _service_context()
    room, host_token, old_player_token, transfer_code = _issued_grant(service)
    room.expires_at = NOW + timedelta(days=2)
    room.host_session_expires_at = NOW + timedelta(days=2)
    repository.save(room)
    original_host = (room.host_session_hash, room.host_csrf_token, room.host_session_expires_at)
    original_room_expiry = room.expires_at
    old_player = room.players[0]
    clock.now_value += timedelta(minutes=1)

    redeemed, new_player_token, new_player_csrf = _redeem(service, room, transfer_code)

    player = redeemed.players[0]
    assert redeemed.version == room.version + 1
    assert player.transfer_code is not None
    assert player.transfer_code.consumed_at == clock.now()
    assert player.session_hash != old_player.session_hash
    assert player.csrf_token == new_player_csrf
    assert new_player_token != old_player_token
    assert player.session_expires_at == original_room_expiry
    assert redeemed.expires_at == original_room_expiry
    assert (
        redeemed.host_session_hash,
        redeemed.host_csrf_token,
        redeemed.host_session_expires_at,
    ) == original_host
    assert redeemed.host_player_id == player.id


@pytest.mark.parametrize("kind", ("wrong", "expired", "old-issued", "consumed"))
def test_invalid_or_unusable_transfer_codes_share_error_and_leave_room_unchanged(kind: str) -> None:
    service, repository, clock = _service_context()
    room, host_token, _, transfer_code = _issued_grant(service)
    if kind == "old-issued":
        _, old_code = room, transfer_code
        room, _ = service.issue_transfer_code(
            room.id,
            room.players[0].id,
            room.version,
            host_token,
            room.host_csrf_token,
            "issue-replacement-code",
        )
        transfer_code = old_code
    elif kind == "expired":
        clock.now_value = room.players[0].transfer_code.expires_at
    elif kind == "consumed":
        room, _, _ = _redeem(service, room, transfer_code, key="consume-before-invalid")

    before = repository.get(room.id)
    assert before is not None
    candidate = "wrong-code" if kind == "wrong" else transfer_code
    with pytest.raises(DomainError) as error:
        _redeem(service, room, candidate, key=f"invalid-{kind}")

    assert error.value.code == "TRANSFER_CODE_INVALID"
    assert repository.get(room.id) == before


def test_valid_transfer_code_with_stale_version_returns_version_conflict() -> None:
    service, _, _ = _service_context()
    room, _, _, transfer_code = _issued_grant(service)

    with pytest.raises(DomainError) as error:
        _redeem(service, room, transfer_code, version=room.version - 1)

    assert error.value.code == "VERSION_CONFLICT"


def test_same_key_replay_returns_the_same_rotated_player_session() -> None:
    service, _, _ = _service_context()
    room, _, _, transfer_code = _issued_grant(service)

    first = _redeem(service, room, transfer_code, key="reassign-replay")
    replay = _redeem(service, room, transfer_code, key="reassign-replay")

    assert replay[1:] == first[1:]


def test_different_keys_concurrently_redeem_at_most_once() -> None:
    service, _, _ = _service_context()
    room, _, _, transfer_code = _issued_grant(service)
    assert hasattr(service, "redeem_transfer_code"), "redeem_transfer_code 尚未建立"

    def attempt(key: str):
        try:
            return "redeemed", _redeem(service, room, transfer_code, key=key)
        except DomainError as error:
            return "rejected", error.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, ("reassign-a", "reassign-b")))

    assert sum(result[0] == "redeemed" for result in results) == 1
    assert sum(result[0] == "rejected" for result in results) == 1


@pytest.mark.parametrize("status", ("COMPLETED", "EXPIRED"))
def test_completed_retention_allows_redeem_but_expired_room_rejects(status: str) -> None:
    service, repository, clock = _service_context()
    room, _, _, transfer_code = _issued_grant(service)
    room.status = status
    if status == "EXPIRED":
        room.expires_at = clock.now()
    repository.save(room)

    if status == "COMPLETED":
        redeemed, _, _ = _redeem(service, room, transfer_code)
        assert redeemed.status == "COMPLETED"
        assert redeemed.expires_at == room.expires_at
    else:
        with pytest.raises(DomainError) as error:
            _redeem(service, room, transfer_code)
        assert error.value.code == "TRANSFER_CODE_INVALID"


def test_reassign_api_rotates_only_local_and_player_cookie_and_revokes_old_player_access() -> None:
    app = create_app(clock=MutableClock(NOW))
    with (
        TestClient(app) as owner,
        TestClient(app) as redeemer,
        TestClient(app) as old_device,
    ):
        created = owner.post(
            "/api/v1/rooms",
            json={"nickname": "房主"},
            headers={"Idempotency-Key": "api-create-reassign"},
        ).json()
        issued = owner.post(
            f"/api/v1/rooms/{created['id']}/players/{created['players'][0]['id']}/transfer-codes",
            json={"room_version": created["version"]},
            headers={
                "Idempotency-Key": "api-issue-reassign",
                "X-CSRF-Token": created["session"]["hostCsrfToken"],
            },
        ).json()
        old_player_cookie = owner.cookies.get("co_story_player")
        host_cookie = owner.cookies.get("co_story_host")
        stored = app.state.room_service.repository.get(created["id"])
        assert stored is not None
        response = redeemer.post(
            f"/api/v1/rooms/{created['id']}/players/{created['players'][0]['id']}:reassign",
            json={"transfer_code": issued["transferCode"], "room_version": stored.version},
            headers={"Idempotency-Key": "api-reassign"},
        )
        new_player_cookie = redeemer.cookies.get("co_story_player")
        current_with_new_cookie = redeemer.get("/api/v1/rooms/current")
        old_device.cookies.set("co_story_local_room", created["id"])
        old_device.cookies.set("co_story_player", old_player_cookie)
        current_with_old_cookie = old_device.get("/api/v1/rooms/current")
        old_action = old_device.put(
            f"/api/v1/rooms/{created['id']}/character",
            json={
                "name": "調查員",
                "background": "熟悉門市每一個角落與所有交班紀錄。",
                "trait": "冷靜",
                "weakness": "猶豫",
                "courage": 2,
                "insight": 1,
                "bond": 0,
                "room_version": stored.version + 1,
            },
            headers={
                "Idempotency-Key": "old-player-action",
                "X-CSRF-Token": created["session"]["csrfToken"],
            },
        )
        owner_after_transfer = owner.get("/api/v1/rooms/current")

    assert response.status_code == 200
    assert host_cookie == owner.cookies.get("co_story_host")
    assert owner_after_transfer.status_code == 200
    assert owner_after_transfer.json()["session"]["isHost"] is True
    assert new_player_cookie != old_player_cookie
    assert current_with_new_cookie.status_code == 200
    assert current_with_old_cookie.status_code == 401
    assert old_action.status_code == 401
    cookies = response.headers.get_list("set-cookie")
    assert any(value.startswith("co_story_local_room=") for value in cookies)
    assert any(value.startswith("co_story_player=") for value in cookies)
    assert all(not value.startswith("co_story_host=") for value in cookies)
