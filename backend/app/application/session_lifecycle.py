from datetime import datetime, timedelta

from app.application.ports import Clock


def is_expired(expires_at: datetime, clock: Clock) -> bool:
    return is_expired_at(expires_at, clock.now())


def is_expired_at(expires_at: datetime, now: datetime) -> bool:
    if expires_at.tzinfo is None or expires_at.utcoffset() != timedelta(0):
        raise ValueError("expires_at must be UTC-aware")
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("clock output must be UTC-aware")
    return now >= expires_at
