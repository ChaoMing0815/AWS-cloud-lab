from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from app.adapters.memory_idempotency_store import MemoryIdempotencyStore
from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.mock_storyteller import MockStoryteller
from app.adapters.postgres_room_repository import _room_from_payload, _room_payload
from app.adapters.secure_dice_roller import SecureDiceRoller
from app.adapters.session_security import HmacSessionTokenFactory
from app.application.room_service import RoomService
from app.domain.models import Player, Room, World


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
EXPIRY = NOW + timedelta(days=7)


def _service(clock: FixedClock | None = None) -> RoomService:
    return RoomService(
        MemoryRoomRepository(),
        MockStoryteller(),
        MemoryIdempotencyStore(),
        HmacSessionTokenFactory(secret=b"test-secret"),
        SecureDiceRoller(),
        clock or FixedClock(NOW),
    )


def _room_with_lifecycle_metadata() -> Room:
    return Room(
        id="room-lifecycle-1",
        room_code="ABC234",
        status="DRAFT",
        version=1,
        round_number=1,
        world=World(name="世界", story_title="故事", premise="前提", objective="目標"),
        expires_at=EXPIRY,
        host_session_expires_at=EXPIRY,
        players=[
            Player(
                id="player-lifecycle-1",
                name="房主",
                role="共同創作者",
                session_expires_at=EXPIRY,
            )
        ],
    )


def test_create_room_initializes_room_and_sessions_from_one_injected_clock() -> None:
    service = _service(clock=FixedClock(NOW))
    room, _, _ = service.create_room("房主", "clocked-create-room")

    assert room.expires_at == EXPIRY
    assert room.host_session_expires_at == EXPIRY
    assert room.players[0].session_expires_at == EXPIRY


def test_postgres_json_payload_round_trips_aware_utc_lifecycle_metadata() -> None:
    payload = _room_payload(_room_with_lifecycle_metadata())

    assert payload["expires_at"] == EXPIRY.isoformat()
    assert payload["host_session_expires_at"] == EXPIRY.isoformat()
    assert payload["players"][0]["session_expires_at"] == EXPIRY.isoformat()

    restored = _room_from_payload(payload)

    assert restored.expires_at == EXPIRY
    assert restored.host_session_expires_at == EXPIRY
    assert restored.players[0].session_expires_at == EXPIRY
    assert restored.expires_at is not None
    assert restored.expires_at.tzinfo is timezone.utc


def test_legacy_postgres_payload_without_lifecycle_metadata_defaults_to_none() -> None:
    payload = asdict(_room_with_lifecycle_metadata())
    payload.pop("expires_at")
    payload.pop("host_session_expires_at")
    payload["players"][0].pop("session_expires_at")

    restored = _room_from_payload(payload)

    assert restored.expires_at is None
    assert restored.host_session_expires_at is None
    assert restored.players[0].session_expires_at is None


def test_demo_room_never_receives_formal_expiry_or_session_metadata() -> None:
    demo_room = _service().load_current(None)

    assert demo_room.expires_at is None
    assert demo_room.host_session_expires_at is None
    assert all(player.session_expires_at is None for player in demo_room.players)
