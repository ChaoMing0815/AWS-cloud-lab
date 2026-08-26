from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from threading import RLock
from typing import Any

from app.application.ports import StoryJobQueue
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

    def __init__(self) -> None:
        self._jobs: dict[str, StoryJob] = {}
        self._idempotency_index: dict[str, str] = {}
        self._lock = RLock()

    @property
    def job_count(self) -> int:
        with self._lock:
            return len(self._jobs)

    def enqueue(self, job: StoryJob) -> StoryJob:
        with self._lock:
            existing_id = self._idempotency_index.get(job.idempotency_key)
            existing_by_id = self._jobs.get(job.job_id)
            existing = self._jobs.get(existing_id) if existing_id else existing_by_id
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
                if current.claimed_by != worker_id:
                    raise StoryJobOwnershipConflict("job is owned by another worker")
                return deepcopy(current)
            if current.status is not StoryJobStatus.PENDING:
                raise StoryJobStateConflict("job cannot be claimed from its current state")
            claimed = replace(
                current,
                status=StoryJobStatus.CLAIMED,
                claimed_by=worker_id,
                attempt_count=current.attempt_count + 1,
            )
            self._jobs[job_id] = claimed
            return deepcopy(claimed)

    def complete(
        self,
        job_id: str,
        worker_id: str,
        result: dict[str, Any],
    ) -> StoryJob:
        if not worker_id:
            raise ValueError("worker_id must not be empty")
        with self._lock:
            current = self._required(job_id)
            if current.status is StoryJobStatus.COMPLETED:
                if current.claimed_by == worker_id and current.result == result:
                    return deepcopy(current)
                raise StoryJobConflict("completed job replay changed owner or result")
            if current.status is not StoryJobStatus.CLAIMED:
                raise StoryJobStateConflict("job must be claimed before completion")
            if current.claimed_by != worker_id:
                raise StoryJobOwnershipConflict("only the claim owner can complete a job")
            completed = replace(
                current,
                status=StoryJobStatus.COMPLETED,
                result=deepcopy(result),
            )
            self._jobs[job_id] = completed
            return deepcopy(completed)

    def _required(self, job_id: str) -> StoryJob:
        try:
            return self._jobs[job_id]
        except KeyError as error:
            raise StoryJobNotFound(job_id) from error
