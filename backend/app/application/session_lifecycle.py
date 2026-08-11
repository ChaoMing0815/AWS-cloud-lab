from datetime import datetime

from app.application.ports import Clock


def is_expired(expires_at: datetime, clock: Clock) -> bool:
    return False
