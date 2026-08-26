from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class StoryJobOperation(str, Enum):
    RESOLVE_ROUND = "resolve-round"


class StoryJobStatus(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    COMPLETED = "completed"


class StoryJobError(Exception):
    """Base error for the local story-job contract."""


class StoryJobNotFound(StoryJobError):
    pass


class StoryJobConflict(StoryJobError):
    pass


class StoryJobOwnershipConflict(StoryJobConflict):
    pass


class StoryJobStateConflict(StoryJobConflict):
    pass


@dataclass(frozen=True)
class StoryJob:
    job_id: str
    idempotency_key: str
    operation: StoryJobOperation
    room_id: str
    round_number: int
    room_version: int
    payload: dict[str, Any]
    status: StoryJobStatus = StoryJobStatus.PENDING
    claimed_by: str | None = None
    attempt_count: int = 0
    result: dict[str, Any] | None = None
