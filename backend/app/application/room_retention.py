from datetime import timedelta

from app.application.ports import Clock, RoomRepository


def cleanup_expired_rooms(repository: RoomRepository, clock: Clock) -> int:
    now = clock.now()
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("clock output must be UTC-aware")
    return repository.delete_expired_at_or_before(now)
