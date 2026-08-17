from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.adapters.memory_idempotency_store import MemoryIdempotencyStore
from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.mock_storyteller import MockStoryteller
from app.adapters.postgres_room_repository import _room_from_payload, _room_payload
from app.adapters.secure_dice_roller import SecureDiceRoller
from app.adapters.session_security import HmacSessionTokenFactory
from app.application.room_service import RoomService
from app.domain.errors import DomainError
from app.domain.models import TransferCode
from app.main import create_app


class MutableClock:
    def __init__(self, now: datetime) -> None:
        self.now_value = now

    def now(self) -> datetime:
        return self.now_value


NOW = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)


def _service_and_clock() -> tuple[RoomService, MemoryRoomRepository, MutableClock]:
    clock = MutableClock(NOW)
    repository = MemoryRoomRepository()
    service = RoomService(
        repository,
        MockStoryteller(),
        MemoryIdempotencyStore(),
        HmacSessionTokenFactory(secret=b"transfer-issuance-test-secret"),
        SecureDiceRoller(),
        clock=clock,
    )
    return service, repository, clock


def _formal_room(service: RoomService):
    return service.create_room("房主", "create-transfer-issuance")


def _issue(
    service: RoomService,
    room,
    host_token: str,
    *,
    key: str = "issue-transfer-code",
    version: int | None = None,
    csrf: str | None = None,
):
    assert hasattr(service, "issue_transfer_code"), "issue_transfer_code 尚未建立"
    return service.issue_transfer_code(
        room.id,
        room.players[0].id,
        room.version if version is None else version,
        host_token,
        room.host_csrf_token if csrf is None else csrf,
        key,
    )


def test_issue_transfer_code_requires_host_csrf_and_current_version() -> None:
    service, _, _ = _service_and_clock()
    room, host_token, _ = _formal_room(service)

    with pytest.raises(DomainError) as bad_host:
        _issue(service, room, "wrong-host-token", key="issue-bad-host")
    with pytest.raises(DomainError) as bad_csrf:
        _issue(service, room, host_token, key="issue-bad-csrf", csrf="wrong-csrf")
    with pytest.raises(DomainError) as stale_version:
        _issue(service, room, host_token, key="issue-stale-version", version=room.version - 1)

    assert bad_host.value.code == "HOST_SESSION_REQUIRED"
    assert bad_csrf.value.code == "CSRF_FAILED"
    assert stale_version.value.code == "VERSION_CONFLICT"


@pytest.mark.parametrize(
    ("room_expiry", "status", "expected_error"),
    [
        (NOW + timedelta(days=1), "LOBBY", None),
        (NOW + timedelta(days=1), "COMPLETED", None),
        (NOW + timedelta(days=1), "UNKNOWN", "TRANSFER_CODE_ISSUE_NOT_ALLOWED"),
        (NOW, "LOBBY", "HOST_SESSION_REQUIRED"),
    ],
    ids=("active-lobby", "completed-retention", "unknown-status", "expired-boundary"),
)
def test_issue_transfer_code_enforces_room_allowlist_and_expiry(
    room_expiry: datetime, status: str, expected_error: str | None
) -> None:
    service, repository, _ = _service_and_clock()
    room, host_token, _ = _formal_room(service)
    persisted = repository.get(room.id)
    assert persisted is not None
    persisted.status = status
    persisted.expires_at = room_expiry
    repository.save(persisted)

    if expected_error:
        with pytest.raises(DomainError) as error:
            _issue(service, persisted, host_token, key=f"issue-{status.lower()}")
        assert error.value.code == expected_error
    else:
        original_room_expiry = persisted.expires_at
        _, raw_code = _issue(service, persisted, host_token)
        assert raw_code
        if status == "COMPLETED":
            stored = repository.get(room.id)
            assert stored is not None
            assert stored.expires_at == original_room_expiry


def test_create_room_records_the_host_player_identity() -> None:
    service, _, _ = _service_and_clock()
    room, _, _ = _formal_room(service)

    assert room.host_player_id == room.players[0].id


def test_issue_transfer_code_stores_only_hash_replaces_prior_code_and_sets_ten_minutes() -> None:
    service, repository, clock = _service_and_clock()
    room, host_token, _ = _formal_room(service)

    first_room, first_raw_code = _issue(service, room, host_token, key="issue-first-code")
    first_metadata = first_room.players[0].transfer_code
    assert first_metadata is not None
    assert first_metadata.code_hash != first_raw_code
    assert first_raw_code not in repr(asdict(first_room))
    assert first_metadata.issued_at == NOW
    assert first_metadata.expires_at == NOW + timedelta(minutes=10)

    clock.now_value += timedelta(minutes=1)
    second_room, second_raw_code = _issue(
        service,
        repository.get(room.id),
        host_token,
        key="issue-second-code",
    )
    second_metadata = second_room.players[0].transfer_code
    assert second_metadata is not None
    assert second_raw_code != first_raw_code
    assert second_metadata.code_hash != first_metadata.code_hash
    assert second_metadata.expires_at == clock.now() + timedelta(minutes=10)
    assert first_raw_code not in repr(asdict(second_room))


def test_same_key_replay_returns_original_code_without_extending_code_expiry() -> None:
    service, _, clock = _service_and_clock()
    room, host_token, _ = _formal_room(service)

    first_room, first_code = _issue(service, room, host_token, key="issue-replay-code")
    first_expiry = first_room.players[0].transfer_code.expires_at
    clock.now_value += timedelta(minutes=1)
    replay_room, replay_code = _issue(service, room, host_token, key="issue-replay-code")

    assert replay_code == first_code
    assert replay_room.players[0].transfer_code.expires_at == first_expiry


def test_different_keys_with_same_version_issue_at_most_one_code() -> None:
    service, _, _ = _service_and_clock()
    room, host_token, _ = _formal_room(service)
    assert hasattr(service, "issue_transfer_code"), "issue_transfer_code 尚未建立"

    def attempt(key: str):
        try:
            return "issued", _issue(service, room, host_token, key=key)
        except DomainError as error:
            return "rejected", error.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, ("issue-concurrent-a", "issue-concurrent-b")))

    assert sum(result[0] == "issued" for result in results) == 1
    assert sum(result[0] == "rejected" for result in results) == 1


def test_nested_transfer_metadata_round_trips_memory_and_postgres_payload() -> None:
    service, repository, _ = _service_and_clock()
    room, _, _ = _formal_room(service)
    room.players[0].transfer_code = TransferCode(
        code_hash="stored-hash-only",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
    )
    repository.save(room)

    memory_restored = repository.get(room.id)
    assert memory_restored == room
    postgres_restored = _room_from_payload(_room_payload(room))
    assert postgres_restored == room


def test_issue_transfer_code_api_returns_plaintext_once_without_setting_session_cookie() -> None:
    with TestClient(create_app(clock=MutableClock(NOW))) as client:
        created = client.post(
            "/api/v1/rooms",
            json={"nickname": "房主"},
            headers={"Idempotency-Key": "create-transfer-api"},
        ).json()
        response = client.post(
            f"/api/v1/rooms/{created['id']}/players/{created['players'][0]['id']}/transfer-codes",
            json={"room_version": created["version"]},
            headers={
                "Idempotency-Key": "issue-transfer-api",
                "X-CSRF-Token": created["session"]["hostCsrfToken"],
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "playerId": created["players"][0]["id"],
        "transferCode": response.json()["transferCode"],
        "expiresAt": (NOW + timedelta(minutes=10)).isoformat(),
        "transfersHostPlayer": True,
        "hostSessionTransferred": False,
    }
    assert response.headers.get_list("set-cookie") == []
