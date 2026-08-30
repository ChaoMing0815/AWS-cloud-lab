from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, timedelta
import json
import logging
from typing import Any

from app.application.ports import (
    StoryJobQueue,
    StoryResolutionNarrator,
    StoryResolutionStore,
    StorytellerFailure,
)
from app.application.rules import ending_cost, ending_result, points_percent, target_points
from app.domain.errors import DomainError
from app.domain.models import Room, StoryEntry
from app.domain.story_resolution import StoryResolutionOutcome, StoryResolutionReceipt


STORYTELLER_SCHEMA_LOGGER = logging.getLogger("co_story.storyteller_schema")


def apply_story_result(
    room: Room,
    result: dict[str, Any],
    *,
    entry_id_factory: Callable[[], str],
    ending_narration_factory: Callable[[Room], str],
) -> tuple[StoryResolutionOutcome, bool]:
    attempts = result.get("attempts", 1)
    if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 1:
        raise StoryResolutionValueError("attempts must be a positive integer")
    failure_code = result.get("failure_code")
    room.resolution_attempts = attempts
    room.resolution_failure_code = failure_code
    if failure_code is not None:
        if not isinstance(failure_code, str) or not failure_code:
            raise StoryResolutionValueError("failure_code must be a non-empty string")
        room.resolution_mode = None
        room.status = "RESOLUTION_FAILED"
        room.version += 1
        return StoryResolutionOutcome.FAILED, False

    narration = result.get("narration")
    if not isinstance(narration, str) or not narration:
        raise StoryResolutionValueError("successful result requires narration")
    results = [
        item for item in room.dice_results if item.round_number == room.round_number
    ]
    room.resolution_mode = "storyteller"
    room.progress_points += sum(item.progress_delta for item in results)
    room.danger_points += sum(item.danger_delta for item in results)
    for item in results:
        player = next(candidate for candidate in room.players if candidate.id == item.player_id)
        if player.character is None:
            raise DomainError("CHARACTER_REQUIRED", "找不到結算所需角色。", 409)
        player.character.spark -= item.spark_used
        if item.result == "FAILURE":
            player.character.spark = min(3, player.character.spark + 1)

    room.entries.append(
        StoryEntry(
            id=entry_id_factory(),
            type="narrator",
            title="故事主持人",
            round_number=room.round_number,
            text=narration,
        )
    )
    for player in room.players:
        player.action = ""
        player.action_approach = ""

    completed = room.round_number >= room.max_rounds
    target = target_points(room.initial_player_count, room.max_rounds)
    progress_percent = points_percent(room.progress_points, target)
    if completed:
        room.ending_result = ending_result(progress_percent)
        room.ending_cost = ending_cost(points_percent(room.danger_points, target))
        room.status = "COMPLETED"
        room.entries.append(
            StoryEntry(
                id=entry_id_factory(),
                type="ending",
                title="故事結局",
                round_number=room.round_number,
                text=ending_narration_factory(room),
            )
        )
    else:
        room.round_number += 1
        room.status = (
            "COMPLETION_AVAILABLE"
            if progress_percent >= 100
            else "COLLECTING_ACTIONS"
        )
    room.version += 1
    return StoryResolutionOutcome.APPLIED, completed


def refresh_story_resolution_activity(
    room: Room,
    *,
    now: datetime,
    completed: bool,
) -> None:
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("story resolution activity clock must be aware UTC")
    activity_expiry = now + timedelta(days=7)
    if completed or room.status != "COMPLETED":
        room.expires_at = activity_expiry
    if room.expires_at is None:
        raise RuntimeError("Formal room expiry is required for session activity")
    room.host_session_expires_at = min(activity_expiry, room.expires_at)


class StoryResolutionValueError(ValueError):
    pass


class StoryResolutionProducer:
    def __init__(self, store: StoryResolutionStore) -> None:
        self._store = store

    def begin(
        self,
        room_id: str,
        round_number: int,
        expected_version: int,
        skip_pending_spark: bool,
    ):
        return self._store.begin_resolution(
            room_id,
            round_number,
            expected_version,
            skip_pending_spark,
        )


class StoryResolutionWorker:
    def __init__(
        self,
        queue: StoryJobQueue,
        store: StoryResolutionStore,
        narrator: StoryResolutionNarrator,
        *,
        max_attempts: int,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        self._queue = queue
        self._store = store
        self._narrator = narrator
        self._max_attempts = max_attempts

    def process(self, job_id: str, worker_id: str) -> StoryResolutionReceipt | Any:
        job = self._queue.claim(job_id, worker_id)
        receipt = self._store.result_for_claim(job)
        if receipt is None:
            try:
                result = self._narrator.resolve(deepcopy(job.payload))
                if not isinstance(result, dict):
                    raise StoryResolutionValueError("narrator result must be a mapping")
                result = deepcopy(result)
                result.setdefault("attempts", job.attempt_count)
            except StorytellerFailure as failure:
                if failure.diagnostic_code is not None:
                    STORYTELLER_SCHEMA_LOGGER.warning(
                        json.dumps(
                            {
                                "operation": job.operation.value,
                                "failure_code": failure.code,
                                "diagnostic_code": failure.diagnostic_code,
                            },
                            separators=(",", ":"),
                        )
                    )
                if failure.retryable and job.attempt_count < self._max_attempts:
                    return self._queue.fail(
                        job.job_id,
                        job.ownership_token or "",
                        failure.code,
                    )
                result = {
                    "failure_code": failure.code,
                    "attempts": job.attempt_count,
                }
            receipt = self._store.commit_result(job, result)

        self._queue.complete(
            job.job_id,
            job.ownership_token or "",
            receipt.completion_result,
        )
        self._store.mark_completion_dispatched(
            job.job_id,
            job.ownership_token or "",
        )
        return receipt
