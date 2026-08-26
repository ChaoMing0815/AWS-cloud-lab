from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

from app.domain.story_jobs import StoryJob, StoryJobOperation


def story_job_idempotency_key(
    operation: StoryJobOperation,
    room_id: str,
    round_number: int,
    room_version: int,
) -> str:
    return (
        f"story:{operation.value}:{room_id}:round:{round_number}:"
        f"version:{room_version}"
    )


def create_story_job(
    *,
    operation: StoryJobOperation,
    room_id: str,
    round_number: int,
    room_version: int,
    payload: dict[str, Any],
    job_id: str | None = None,
) -> StoryJob:
    if not room_id:
        raise ValueError("room_id must not be empty")
    if round_number < 1:
        raise ValueError("round_number must be positive")
    if room_version < 0:
        raise ValueError("room_version must not be negative")
    resolved_job_id = job_id or str(uuid4())
    if not resolved_job_id:
        raise ValueError("job_id must not be empty")
    return StoryJob(
        job_id=resolved_job_id,
        idempotency_key=story_job_idempotency_key(
            operation,
            room_id,
            round_number,
            room_version,
        ),
        operation=operation,
        room_id=room_id,
        round_number=round_number,
        room_version=room_version,
        payload=deepcopy(payload),
    )
