from __future__ import annotations

import os
import sys
import threading
from datetime import timedelta
from uuid import uuid4

from app.adapters.mock_storyteller import MockStoryteller
from app.adapters.postgres_story_job_queue import PostgresStoryJobQueue
from app.adapters.postgres_story_resolution_store import PostgresStoryResolutionStore
from app.adapters.story_resolution_narrator import StorytellerSnapshotNarrator
from app.adapters.system_clock import SystemClock
from app.application.story_resolution import StoryResolutionWorker
from app.domain.story_jobs import StoryJob, StoryJobStatus


class LocalStoryResolutionWorkerRunner:
    def __init__(self, queue, worker, *, worker_id: str) -> None:
        if not worker_id:
            raise ValueError("worker_id must not be empty")
        self._queue = queue
        self._worker = worker
        self._worker_id = worker_id

    def run_once(self) -> str:
        job_id = self._queue.next_available_job_id()
        if job_id is None:
            return "idle"
        self._worker.process(job_id, self._worker_id)
        return "processed"


class SqsStoryResolutionWorkerRunner:
    def __init__(
        self,
        transport,
        worker,
        *,
        worker_id: str,
        heartbeat_factory=None,
    ) -> None:
        if not worker_id:
            raise ValueError("worker_id must not be empty")
        self._transport = transport
        self._worker = worker
        self._worker_id = worker_id
        self._heartbeat_factory = heartbeat_factory or transport.visibility_heartbeat

    def run_once(self) -> str:
        delivery = self._transport.receive_one()
        if delivery is None:
            return "idle"
        with self._heartbeat_factory(delivery):
            result = self._worker.process(delivery.job_id, self._worker_id)
        if isinstance(result, StoryJob) and result.status is StoryJobStatus.PENDING:
            return "retry"
        self._transport.delete(delivery)
        return "processed"

    def run_forever(self, *, stop_event=None) -> str:
        resolved_stop_event = stop_event or threading.Event()
        while not resolved_stop_event.is_set():
            self.run_once()
        return "stopped"


def build_local_runner(dsn: str, *, worker_id: str | None = None):
    if not dsn:
        raise ValueError("DATABASE_URL is required")
    clock = SystemClock()
    queue = PostgresStoryJobQueue(
        dsn,
        clock=clock,
        lease_duration=timedelta(seconds=30),
        max_attempts=2,
    )
    store = PostgresStoryResolutionStore(dsn, clock=clock)
    narrator = StorytellerSnapshotNarrator(MockStoryteller())
    worker = StoryResolutionWorker(queue, store, narrator, max_attempts=2)
    return LocalStoryResolutionWorkerRunner(
        queue,
        worker,
        worker_id=worker_id or f"local-worker-{uuid4().hex}",
    )


def build_production_runner(dsn: str, *, worker_id: str | None = None):
    from app.adapters.production_storyteller_factory import build_production_worker

    return build_production_worker(
        dsn,
        worker_id=worker_id or f"production-worker-{uuid4().hex}",
    )


def _build_runner(dsn: str, *, worker_id: str | None = None):
    if os.environ.get("CO_STORY_ENV", "").lower() == "production":
        return build_production_runner(dsn, worker_id=worker_id)
    return build_local_runner(dsn, worker_id=worker_id)


def main() -> int:
    dsn = os.environ.get("DATABASE_URL", "")
    if not dsn:
        print("worker_result=stopped:database_url_missing")
        return 2
    try:
        runner = _build_runner(dsn)
        if os.environ.get("CO_STORY_ENV", "").lower() == "production":
            result = runner.run_forever()
        else:
            result = runner.run_once()
    except RuntimeError as error:
        print(f"worker_result=stopped:{error}")
        return 2
    except Exception:
        print("worker_result=stopped:worker_bootstrap_failure")
        return 2
    print(f"worker_result={result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
