from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import RLock
from typing import Any
from uuid import uuid4

from app.application.ports import Clock, StoryResolutionStore
from app.application.story_jobs import create_story_job, story_job_idempotency_key
from app.application.story_resolution import apply_story_result, refresh_story_resolution_activity
from app.domain.models import Room
from app.domain.story_jobs import StoryJob, StoryJobOperation, StoryJobStatus
from app.domain.story_resolution import (
    StoryResolutionConflict,
    StoryResolutionOutcome,
    StoryResolutionOwnershipConflict,
    StoryResolutionReceipt,
    StoryResolutionStateConflict,
    build_story_resolution_snapshot,
    story_result_fingerprint,
)


@dataclass
class _CompletionOutbox:
    job_id: str
    ownership_token: str
    completion_payload: dict[str, Any]
    dispatched_at: datetime | None = None


class MemoryStoryResolutionStore(StoryResolutionStore):
    """Transactional contract double; it is not a durable production store."""

    def __init__(
        self,
        rooms: list[Room],
        *,
        clock: Clock,
        job_id_factory=None,
        entry_id_factory=None,
        fault_hook=None,
    ) -> None:
        self._rooms = {room.id: deepcopy(room) for room in rooms}
        self._jobs: dict[str, StoryJob] = {}
        self._receipts: dict[str, StoryResolutionReceipt] = {}
        self._outbox: dict[str, _CompletionOutbox] = {}
        self._claims: dict[str, tuple[int, str, datetime]] = {}
        self._clock = clock
        self._job_id_factory = job_id_factory or (lambda: str(uuid4()))
        self._entry_id_factory = entry_id_factory or (lambda: str(uuid4()))
        self._fault_hook = fault_hook or (lambda point: None)
        self._lock = RLock()

    def begin_resolution(
        self,
        room_id: str,
        round_number: int,
        expected_version: int,
        skip_pending_spark: bool,
    ) -> StoryJob:
        with self._lock:
            snapshot = self._snapshot_state()
            try:
                expected_job_version = expected_version + 1
                key = story_job_idempotency_key(
                    StoryJobOperation.RESOLVE_ROUND,
                    room_id,
                    round_number,
                    expected_job_version,
                )
                existing = next(
                    (job for job in self._jobs.values() if job.idempotency_key == key),
                    None,
                )
                if existing is not None:
                    producer = existing.payload.get("producer", {})
                    if (
                        existing.operation is not StoryJobOperation.RESOLVE_ROUND
                        or existing.room_id != room_id
                        or existing.round_number != round_number
                        or existing.room_version != expected_job_version
                        or producer
                        != {
                            "source_room_version": expected_version,
                            "skip_pending_spark": skip_pending_spark,
                        }
                    ):
                        raise StoryResolutionConflict("producer replay changed input")
                    return deepcopy(existing)

                room = self._rooms.get(room_id)
                if room is None:
                    raise StoryResolutionStateConflict("room not found")
                if room.version != expected_version:
                    raise StoryResolutionStateConflict("room version conflict")
                if room.round_number != round_number:
                    raise StoryResolutionStateConflict("round mismatch")
                if room.status not in {"AWAITING_SPARK", "RESOLVING", "RESOLUTION_FAILED"}:
                    raise StoryResolutionStateConflict("room cannot begin resolution")
                results = [
                    item for item in room.dice_results if item.round_number == round_number
                ]
                pending = [item for item in results if item.spark_decision == "PENDING"]
                if pending and not skip_pending_spark:
                    raise StoryResolutionStateConflict("spark decisions are pending")
                for item in pending:
                    item.spark_decision = "DECLINE"
                room.status = "RESOLVING"
                room.version += 1
                payload = build_story_resolution_snapshot(
                    room,
                    source_room_version=expected_version,
                    skip_pending_spark=skip_pending_spark,
                )
                job = create_story_job(
                    operation=StoryJobOperation.RESOLVE_ROUND,
                    room_id=room.id,
                    round_number=round_number,
                    room_version=room.version,
                    payload=payload,
                    job_id=self._job_id_factory(),
                )
                self._fault_hook("after_room_cas")
                self._jobs[job.job_id] = deepcopy(job)
                self._fault_hook("after_job_insert")
                return deepcopy(job)
            except Exception:
                self._restore_state(snapshot)
                raise

    def result_for_claim(self, job: StoryJob) -> StoryResolutionReceipt | None:
        with self._lock:
            self._validate_claim(job, register=True)
            receipt = self._receipts.get(job.job_id)
            if receipt is not None:
                outbox = self._outbox[job.job_id]
                if outbox.dispatched_at is None:
                    outbox.ownership_token = job.ownership_token or ""
                return deepcopy(receipt)
            return None

    def commit_result(
        self,
        job: StoryJob,
        result: dict[str, Any],
    ) -> StoryResolutionReceipt:
        with self._lock:
            snapshot = self._snapshot_state()
            try:
                self._validate_claim(job, register=False)
                fingerprint = story_result_fingerprint(result)
                existing = self._receipts.get(job.job_id)
                if existing is not None:
                    if existing.result_fingerprint != fingerprint:
                        raise StoryResolutionConflict("result replay diverged")
                    outbox = self._outbox[job.job_id]
                    if outbox.dispatched_at is None:
                        outbox.ownership_token = job.ownership_token or ""
                    return deepcopy(existing)

                room = self._rooms.get(job.room_id)
                if room is None:
                    raise StoryResolutionStateConflict("room not found")
                if (
                    room.version != job.room_version
                    or room.round_number != job.round_number
                    or room.status != "RESOLVING"
                ):
                    outcome = StoryResolutionOutcome.STALE
                    room_version_after = None
                else:
                    outcome, completed = apply_story_result(
                        room,
                        deepcopy(result),
                        entry_id_factory=self._entry_id_factory,
                        ending_narration_factory=lambda current: _required_ending(result),
                    )
                    refresh_story_resolution_activity(
                        room,
                        now=self._utc_now(),
                        completed=completed,
                    )
                    room_version_after = room.version
                    self._fault_hook("after_room_result")

                receipt = StoryResolutionReceipt.create(
                    job=job,
                    outcome=outcome,
                    result=result,
                    room_version_after=room_version_after,
                )
                self._receipts[job.job_id] = deepcopy(receipt)
                self._fault_hook("after_inbox_insert")
                self._outbox[job.job_id] = _CompletionOutbox(
                    job_id=job.job_id,
                    ownership_token=job.ownership_token or "",
                    completion_payload=receipt.completion_result,
                )
                self._fault_hook("after_outbox_insert")
                return deepcopy(receipt)
            except Exception:
                self._restore_state(snapshot)
                raise

    def mark_completion_dispatched(
        self,
        job_id: str,
        ownership_token: str,
    ) -> None:
        with self._lock:
            outbox = self._outbox.get(job_id)
            if outbox is None:
                raise StoryResolutionStateConflict("completion outbox not found")
            if outbox.ownership_token != ownership_token:
                raise StoryResolutionOwnershipConflict("completion token changed")
            if outbox.dispatched_at is None:
                outbox.dispatched_at = self._utc_now()

    def room(self, room_id: str) -> Room | None:
        with self._lock:
            return deepcopy(self._rooms.get(room_id))

    def job(self, job_id: str) -> StoryJob | None:
        with self._lock:
            return deepcopy(self._jobs.get(job_id))

    def receipt(self, job_id: str) -> StoryResolutionReceipt | None:
        with self._lock:
            return deepcopy(self._receipts.get(job_id))

    def outbox(self, job_id: str):
        with self._lock:
            return deepcopy(self._outbox.get(job_id))

    def _validate_claim(self, job: StoryJob, *, register: bool) -> None:
        now = self._utc_now()
        if job.status is not StoryJobStatus.CLAIMED:
            raise StoryResolutionStateConflict("result requires a claimed job")
        if not job.ownership_token:
            raise StoryResolutionOwnershipConflict("claim has no ownership token")
        if job.lease_expires_at is None or now >= job.lease_expires_at:
            raise StoryResolutionOwnershipConflict("claim lease expired")
        current = self._claims.get(job.job_id)
        if current is not None:
            attempt, token, _ = current
            if job.attempt_count < attempt or (
                job.attempt_count == attempt and job.ownership_token != token
            ):
                raise StoryResolutionOwnershipConflict("claim was fenced")
        if register and (current is None or job.attempt_count > current[0]):
            self._claims[job.job_id] = (
                job.attempt_count,
                job.ownership_token,
                job.lease_expires_at,
            )
        elif not register:
            if current is None or current[:2] != (job.attempt_count, job.ownership_token):
                raise StoryResolutionOwnershipConflict("claim was not prepared")

    def _utc_now(self) -> datetime:
        now = self._clock.now()
        if now.tzinfo is None or now.utcoffset() != timedelta(0):
            raise ValueError("clock must return aware UTC")
        return now

    def _snapshot_state(self):
        return deepcopy(
            (self._rooms, self._jobs, self._receipts, self._outbox, self._claims)
        )

    def _restore_state(self, snapshot) -> None:
        (
            self._rooms,
            self._jobs,
            self._receipts,
            self._outbox,
            self._claims,
        ) = snapshot


def _required_ending(result: dict[str, Any]) -> str:
    narration = result.get("ending_narration")
    if not isinstance(narration, str) or not narration:
        raise StoryResolutionStateConflict("final round requires ending narration")
    return narration
