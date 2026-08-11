from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

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


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


NOW = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)


def _service_context() -> tuple[RoomService, MemoryRoomRepository]:
    repository = MemoryRoomRepository()
    service = RoomService(
        repository,
        MockStoryteller(),
        MemoryIdempotencyStore(),
        HmacSessionTokenFactory(secret=b"room-deletion-test-secret"),
        SecureDiceRoller(),
        clock=FixedClock(NOW),
    )
    return service, repository


def _room_with_transfer(service: RoomService):
    room, host_token, player_token = service.create_room("房主", "create-delete-room")
    issued, transfer_code = service.issue_transfer_code(
        room.id,
        room.players[0].id,
        room.version,
        host_token,
        room.host_csrf_token,
        "issue-before-delete",
    )
    return issued, host_token, player_token, transfer_code


def _delete(
    service: RoomService,
    room,
    host_token: str,
    *,
    key: str = "delete-room",
    version: int | None = None,
    csrf: str | None = None,
):
    assert hasattr(service, "delete_room"), "delete_room 尚未建立"
    return service.delete_room(
        room.id,
        room.version if version is None else version,
        host_token,
        room.host_csrf_token if csrf is None else csrf,
        key,
    )


def test_delete_room_atomically_removes_aggregate_and_disables_old_sessions_and_transfer() -> None:
    service, repository = _service_context()
    room, host_token, player_token, transfer_code = _room_with_transfer(service)

    _delete(service, room, host_token)

    assert repository.get(room.id) is None
    assert repository.get_by_code(room.room_code) is None
    with pytest.raises(DomainError) as current:
        service.current_session_summary(room.id, host_token, player_token)
    with pytest.raises(DomainError) as old_transfer:
        service.redeem_transfer_code(
            room.id,
            room.players[0].id,
            transfer_code,
            room.version,
            "redeem-after-delete",
        )
    assert current.value.code == "SESSION_NOT_FOUND"
    assert old_transfer.value.code == "TRANSFER_CODE_INVALID"


@pytest.mark.parametrize("kind", ("expired-host", "wrong-csrf", "stale-version"))
def test_delete_precedence_rejects_invalid_request_without_deleting(kind: str) -> None:
    service, repository = _service_context()
    room, host_token, _, _ = _room_with_transfer(service)
    if kind == "expired-host":
        room.host_session_expires_at = NOW
        repository.save(room)
        host_token = "wrong-host-token"
    kwargs = {
        "csrf": "wrong-csrf" if kind == "wrong-csrf" else None,
        "version": room.version - 1 if kind == "stale-version" else None,
    }

    with pytest.raises(DomainError) as error:
        _delete(service, room, host_token, key=f"delete-{kind}", **kwargs)

    assert error.value.code == {
        "expired-host": "HOST_SESSION_REQUIRED",
        "wrong-csrf": "CSRF_FAILED",
        "stale-version": "VERSION_CONFLICT",
    }[kind]
    assert repository.get(room.id) == room


def test_delete_same_key_replay_succeeds_but_different_concurrent_keys_delete_once() -> None:
    service, _ = _service_context()
    room, host_token, _, _ = _room_with_transfer(service)

    assert _delete(service, room, host_token, key="delete-replay") is None
    assert _delete(service, room, host_token, key="delete-replay") is None

    service, _ = _service_context()
    room, host_token, _, _ = _room_with_transfer(service)
    assert hasattr(service, "delete_room"), "delete_room 尚未建立"

    def attempt(key: str):
        try:
            _delete(service, room, host_token, key=key)
            return "deleted"
        except DomainError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, ("delete-concurrent-a", "delete-concurrent-b")))

    assert results.count("deleted") == 1


def test_memory_delete_rolls_back_when_validation_callback_raises() -> None:
    service, repository = _service_context()
    room, _, _, _ = _room_with_transfer(service)
    assert hasattr(repository, "delete"), "RoomRepository.delete 尚未建立"

    with pytest.raises(RuntimeError, match="abort deletion"):
        repository.delete(room.id, lambda _room: (_ for _ in ()).throw(RuntimeError("abort deletion")))

    assert repository.get(room.id) == room


def test_delete_api_returns_empty_204_and_clears_all_room_session_cookies() -> None:
    app = create_app(clock=FixedClock(NOW))
    with TestClient(app) as client, TestClient(app) as old_device:
        created = client.post(
            "/api/v1/rooms",
            json={"nickname": "房主"},
            headers={"Idempotency-Key": "api-create-delete"},
        ).json()
        host_cookie = client.cookies.get("co_story_host")
        player_cookie = client.cookies.get("co_story_player")
        response = client.request(
            "DELETE",
            f"/api/v1/rooms/{created['id']}",
            json={"room_version": created["version"]},
            headers={
                "Idempotency-Key": "api-delete-room",
                "X-CSRF-Token": created["session"]["hostCsrfToken"],
            },
        )
        old_device.cookies.set("co_story_local_room", created["id"])
        old_device.cookies.set("co_story_host", host_cookie)
        old_device.cookies.set("co_story_player", player_cookie)
        current = old_device.get("/api/v1/rooms/current")

    assert response.status_code == 204
    assert response.content == b""
    assert current.status_code == 401
    cookies = response.headers.get_list("set-cookie")
    for name in ("co_story_local_room", "co_story_host", "co_story_player"):
        assert any(value.startswith(f"{name}=") and "Max-Age=0" in value for value in cookies)
