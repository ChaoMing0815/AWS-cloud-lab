import importlib
import importlib.util
from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.domain.models import Room, World


NOW = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


def _room(room_id: str, expires_at: datetime | None, status: str = "AWAITING_SPARK") -> Room:
    return Room(
        id=room_id,
        room_code=f"C{room_id[-5:].upper()}",
        status=status,
        version=1,
        round_number=1,
        world=World("測試世界", "測試故事", "前提", "目標"),
        expires_at=expires_at,
    )


def _cleanup(repository: MemoryRoomRepository, clock: FixedClock) -> int:
    spec = importlib.util.find_spec("app.application.room_retention")
    assert spec is not None, "到期房間 cleanup use case 尚未建立"
    module = importlib.import_module("app.application.room_retention")
    cleanup = getattr(module, "cleanup_expired_rooms", None)
    assert callable(cleanup), "cleanup_expired_rooms() 尚未建立"
    return cleanup(repository, clock)


def test_retention_cleanup_removes_all_statuses_at_or_before_utc_boundary() -> None:
    repository = MemoryRoomRepository()
    expired = (
        _room("expired-draft", NOW - timedelta(seconds=1), "DRAFT"),
        _room("expired-lobby", NOW, "LOBBY"),
        _room("expired-round", NOW - timedelta(days=1), "AWAITING_SPARK"),
        _room("expired-completed", NOW, "COMPLETED"),
    )
    preserved = (
        _room("future", NOW + timedelta(microseconds=1)),
        _room("demo", None),
    )
    for room in (*expired, *preserved):
        repository.save(room)

    assert _cleanup(repository, FixedClock(NOW)) == len(expired)
    assert all(repository.get(room.id) is None for room in expired)
    assert all(repository.get(room.id) is not None for room in preserved)


def test_retention_cleanup_is_repeatable_after_expired_rooms_are_removed() -> None:
    repository = MemoryRoomRepository()
    repository.save(_room("expired", NOW))

    assert _cleanup(repository, FixedClock(NOW)) == 1
    assert _cleanup(repository, FixedClock(NOW)) == 0


def test_retention_cleanup_rejects_naive_clock_before_deleting_rooms() -> None:
    repository = MemoryRoomRepository()
    expired = _room("expired", NOW - timedelta(seconds=1))
    repository.save(expired)

    with pytest.raises(ValueError, match="UTC-aware"):
        _cleanup(repository, FixedClock(NOW.replace(tzinfo=None)))

    assert repository.get(expired.id) is not None
