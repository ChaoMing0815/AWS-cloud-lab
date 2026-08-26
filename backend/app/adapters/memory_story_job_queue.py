from __future__ import annotations

import secrets
from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta
from threading import RLock
from typing import Any

from app.application.ports import Clock, StoryJobQueue
from app.domain.story_jobs import (
    StoryJob,
    StoryJobConflict,
    StoryJobNotFound,
    StoryJobOwnershipConflict,
    StoryJobStateConflict,
    StoryJobStatus,
)


class MemoryStoryJobQueue(StoryJobQueue):
    """Process-local contract double; it provides no durable exactly-once guarantee."""

    def __init__(
        self,
        *,
        clock: Clock,
        lease_duration: timedelta,
        max_attempts: int,
        ownership_token_factory: Callable[[], str] | None = None,
    ) -> None:
        if lease_duration <= timedelta(0):
            raise ValueError("lease_duration must be positive")
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        self._clock = clock
        self._lease_duration = lease_duration
        self._max_attempts = max_attempts
        self._ownership_token_factory = (
            ownership_token_factory or (lambda: secrets.token_urlsafe(32))
        )
        self._jobs: dict[str, StoryJob] = {}
        self._idempotency_index: dict[str, str] = {}
        self._issued_tokens: set[str] = set()
        self._lock = RLock()

    @property
    def job_count(self) -> int:
        with self._lock:
            return len(self._jobs)

    def enqueue(self, job: StoryJob) -> StoryJob:
        with self._lock:
            existing_id = self._idempotency_index.get(job.idempotency_key)
            existing_by_id = self._jobs.get(job.job_id)
            existing_by_key = self._jobs.get(existing_id) if existing_id else None
            if (
                existing_by_id is not None
                and existing_by_key is not None
                and existing_by_id.job_id != existing_by_key.job_id
            ):
                raise StoryJobConflict(
                    "job id and idempotency key resolve to different jobs"
                )
            existing = existing_by_key or existing_by_id
            if existing is not None:
                if existing != job:
                    raise StoryJobConflict("idempotency key or job id reused")
                return deepcopy(existing)
            if job.status is not StoryJobStatus.PENDING:
                raise StoryJobStateConflict("only pending jobs can be enqueued")
            stored = deepcopy(job)
            self._jobs[job.job_id] = stored
            self._idempotency_index[job.idempotency_key] = job.job_id
            return deepcopy(stored)

    def claim(self, job_id: str, worker_id: str) -> StoryJob:
        if not worker_id:
            raise ValueError("worker_id must not be empty")
        with self._lock:
            current = self._required(job_id)
            if current.status is StoryJobStatus.CLAIMED:
                now = self._utc_now()
                if current.lease_expires_at is not None and now < current.lease_expires_at:
                    if current.claimed_by != worker_id:
                        raise StoryJobOwnershipConflict("job is owned by another worker")
                    return deepcopy(current)
                if current.attempt_count >= self._max_attempts:
                    terminal = replace(
                        current,
                        status=StoryJobStatus.DEAD_LETTERED,
                        claimed_by=None,
                        ownership_token=None,
                        lease_expires_at=None,
                        terminal_error="LEASE_EXPIRED",
                    )
                    self._jobs[job_id] = terminal
                    return deepcopy(terminal)
            if current.status is not StoryJobStatus.PENDING:
                if current.status is not StoryJobStatus.CLAIMED:
                    raise StoryJobStateConflict("job cannot be claimed from its current state")
            now = self._utc_now()
            claimed = replace(
                current,
                status=StoryJobStatus.CLAIMED,
                claimed_by=worker_id,
                ownership_token=self._new_ownership_token(),
                lease_expires_at=now + self._lease_duration,
                attempt_count=current.attempt_count + 1,
                terminal_error=None,
            )
            self._jobs[job_id] = claimed
            return deepcopy(claimed)

    def complete(
        self,
        job_id: str,
        ownership_token: str,
        result: dict[str, Any],
    ) -> StoryJob:
        if not ownership_token:
            raise ValueError("ownership_token must not be empty")
        with self._lock:
            current = self._required(job_id)
            if current.status is StoryJobStatus.COMPLETED:
                if current.ownership_token == ownership_token and current.result == result:
                    return deepcopy(current)
                raise StoryJobConflict("completed job replay changed owner or result")
            if current.status is not StoryJobStatus.CLAIMED:
                raise StoryJobStateConflict("job must be claimed before completion")
            self._require_active_token(current, ownership_token)
            completed = replace(
                current,
                status=StoryJobStatus.COMPLETED,
                lease_expires_at=None,
                result=deepcopy(result),
            )
            self._jobs[job_id] = completed
            return deepcopy(completed)

    def fail(
        self,
        job_id: str,
        ownership_token: str,
        error_code: str,
    ) -> StoryJob:
        if not ownership_token:
            raise ValueError("ownership_token must not be empty")
        if not error_code:
            raise ValueError("error_code must not be empty")
        with self._lock:
            current = self._required(job_id)
            if current.status is not StoryJobStatus.CLAIMED:
                raise StoryJobStateConflict("only claimed jobs can fail")
            self._require_active_token(current, ownership_token)
            exhausted = current.attempt_count >= self._max_attempts
            failed = replace(
                current,
                status=(
                    StoryJobStatus.DEAD_LETTERED
                    if exhausted
                    else StoryJobStatus.PENDING
                ),
                claimed_by=None,
                ownership_token=None,
                lease_expires_at=None,
                terminal_error=error_code if exhausted else None,
            )
            self._jobs[job_id] = failed
            return deepcopy(failed)

    def _require_active_token(
        self,
        job: StoryJob,
        ownership_token: str,
    ) -> None:
        if job.ownership_token != ownership_token:
            raise StoryJobOwnershipConflict("operation requires the current fencing token")
        if job.lease_expires_at is None or self._utc_now() >= job.lease_expires_at:
            raise StoryJobOwnershipConflict("expired fencing token cannot mutate a job")

    def _utc_now(self) -> datetime:
        now = self._clock.now()
        if now.tzinfo is None or now.utcoffset() != timedelta(0):
            raise ValueError("clock must return an aware UTC datetime")
        return now

    def _new_ownership_token(self) -> str:
        token = self._ownership_token_factory()
        if not token or token in self._issued_tokens:
            raise RuntimeError("ownership token factory must return unique non-empty tokens")
        self._issued_tokens.add(token)
        return token

    def _required(self, job_id: str) -> StoryJob:
        try:
            return self._jobs[job_id]
        except KeyError as error:
            raise StoryJobNotFound(job_id) from error
