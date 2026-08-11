from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.system_clock import SystemClock
from app.application.ports import Clock
from app.application.session_lifecycle import is_expired


class FixedClock(Clock):
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("expires_at", "expected"),
    [
        (NOW + timedelta(microseconds=1), False),
        (NOW, True),
        (NOW - timedelta(microseconds=1), True),
    ],
    ids=("before-expiry", "at-expiry", "after-expiry"),
)
def test_expiry_uses_utc_boundary_comparison(expires_at: datetime, expected: bool) -> None:
    assert is_expired(expires_at, FixedClock(NOW)) is expected


def test_system_clock_returns_aware_utc_time() -> None:
    now = SystemClock().now()

    assert now.tzinfo is timezone.utc
    assert now.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    "expires_at, clock_now",
    [
        (datetime(2026, 8, 11, 12, 0), NOW),
        (NOW, datetime(2026, 8, 11, 12, 0)),
    ],
    ids=("naive-expiry", "naive-clock-output"),
)
def test_expiry_rejects_naive_times(expires_at: datetime, clock_now: datetime) -> None:
    with pytest.raises(ValueError, match="UTC-aware"):
        is_expired(expires_at, FixedClock(clock_now))
