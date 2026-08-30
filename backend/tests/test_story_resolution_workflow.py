from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib
import importlib.util
import json
import logging

import pytest

from app.application.ports import StorytellerFailure
from app.application.story_jobs import create_story_job
from app.domain.story_jobs import StoryJobOperation, StoryJobStatus


NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def _module():
    spec = importlib.util.find_spec("app.application.story_resolution")
    assert spec is not None, "story resolution application slice 尚未建立"
    return importlib.import_module("app.application.story_resolution")


def claimed_job(*, token="token-1", attempt=1, payload=None):
    pending = create_story_job(
        operation=StoryJobOperation.RESOLVE_ROUND,
        room_id="room-1",
        round_number=2,
        room_version=8,
        payload=payload or {"world": {"name": "霽霧之城"}},
        job_id="job-1",
    )
    return replace(
        pending,
        status=StoryJobStatus.CLAIMED,
        claimed_by="worker-1",
        ownership_token=token,
        lease_expires_at=NOW + timedelta(seconds=30),
        attempt_count=attempt,
    )


class ScriptedQueue:
    def __init__(self, job, *, complete_error=None):
        self.job = job
        self.complete_error = complete_error
        self.events = []

    def claim(self, job_id, worker_id):
        self.events.append("claim")
        return self.job

    def complete(self, job_id, token, result):
        self.events.append(("complete", deepcopy(result)))
        if self.complete_error:
            raise self.complete_error
        return replace(self.job, status=StoryJobStatus.COMPLETED, lease_expires_at=None, result=deepcopy(result))

    def fail(self, job_id, token, error_code):
        self.events.append(("fail", error_code))
        return replace(self.job, status=StoryJobStatus.PENDING, claimed_by=None, ownership_token=None, lease_expires_at=None)


class ScriptedStore:
    def __init__(self, module, *, existing=None, commit_error=None):
        self.module = module
        self.existing = existing
        self.commit_error = commit_error
        self.events = []
        self.committed = None

    def result_for_claim(self, job):
        self.events.append("inbox")
        return self.existing

    def commit_result(self, job, result):
        self.events.append("data_commit")
        if self.commit_error:
            raise self.commit_error
        self.committed = deepcopy(result)
        outcome = (
            self.module.StoryResolutionOutcome.FAILED
            if result.get("failure_code")
            else self.module.StoryResolutionOutcome.APPLIED
        )
        return self.module.StoryResolutionReceipt.create(
            job=job,
            outcome=outcome,
            result=result,
            room_version_after=9,
        )

    def mark_completion_dispatched(self, job_id, token):
        self.events.append("dispatched")


class Narrator:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []

    def resolve(self, snapshot):
        self.calls.append(deepcopy(snapshot))
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return deepcopy(self.outcome)


def test_worker_has_no_session_inputs_calls_storyteller_once_and_commits_before_ack() -> None:
    module = _module()
    job = claimed_job()
    queue = ScriptedQueue(job)
    store = ScriptedStore(module)
    narrator = Narrator({"narration": "燈塔恢復了一部分光芒。"})
    worker = module.StoryResolutionWorker(queue, store, narrator, max_attempts=2)

    receipt = worker.process("job-1", "worker-1")

    assert len(narrator.calls) == 1
    assert not any("session" in key.lower() for key in narrator.calls[0])
    assert store.events == ["inbox", "data_commit", "dispatched"]
    assert queue.events[0] == "claim"
    assert queue.events[1][0] == "complete"
    assert receipt.outcome is module.StoryResolutionOutcome.APPLIED


def test_data_rollback_never_acknowledges_queue() -> None:
    module = _module()
    queue = ScriptedQueue(claimed_job())
    store = ScriptedStore(module, commit_error=RuntimeError("injected data rollback"))
    worker = module.StoryResolutionWorker(queue, store, Narrator({"narration": "result"}), max_attempts=2)

    with pytest.raises(RuntimeError, match="data rollback"):
        worker.process("job-1", "worker-1")

    assert queue.events == ["claim"]
    assert store.events == ["inbox", "data_commit"]


def test_commit_then_ack_failure_replays_inbox_without_second_storyteller_call() -> None:
    module = _module()
    job = claimed_job()
    first_queue = ScriptedQueue(job, complete_error=RuntimeError("ack unavailable"))
    store = ScriptedStore(module)
    narrator = Narrator({"narration": "canonical"})
    worker = module.StoryResolutionWorker(first_queue, store, narrator, max_attempts=2)

    with pytest.raises(RuntimeError, match="ack unavailable"):
        worker.process("job-1", "worker-1")
    receipt = module.StoryResolutionReceipt.create(
        job=job,
        outcome=module.StoryResolutionOutcome.APPLIED,
        result=store.committed,
        room_version_after=9,
    )
    reclaimed = replace(job, claimed_by="worker-2", ownership_token="token-2", attempt_count=2)
    replay_queue = ScriptedQueue(reclaimed)
    replay_store = ScriptedStore(module, existing=receipt)
    replay_worker = module.StoryResolutionWorker(replay_queue, replay_store, narrator, max_attempts=2)

    replayed = replay_worker.process("job-1", "worker-2")

    assert len(narrator.calls) == 1
    assert replayed.result_fingerprint == receipt.result_fingerprint
    assert replay_store.events == ["inbox", "dispatched"]
    assert replay_queue.events[1][0] == "complete"


@pytest.mark.parametrize("code", ["TIMEOUT", "THROTTLED", "TRANSIENT_SERVICE_ERROR", "SCHEMA_INVALID"])
def test_retryable_failure_returns_to_durable_queue_before_max_attempt(code) -> None:
    module = _module()
    queue = ScriptedQueue(claimed_job(attempt=1))
    store = ScriptedStore(module)
    narrator = Narrator(StorytellerFailure(code))
    worker = module.StoryResolutionWorker(queue, store, narrator, max_attempts=2)

    worker.process("job-1", "worker-1")

    assert len(narrator.calls) == 1
    assert queue.events == ["claim", ("fail", code)]
    assert store.events == ["inbox"]


def test_nonretryable_failure_is_committed_once_as_terminal_result() -> None:
    module = _module()
    queue = ScriptedQueue(claimed_job())
    store = ScriptedStore(module)
    worker = module.StoryResolutionWorker(
        queue,
        store,
        Narrator(StorytellerFailure("CONTENT_REJECTED")),
        max_attempts=2,
    )

    receipt = worker.process("job-1", "worker-1")

    assert receipt.outcome is module.StoryResolutionOutcome.FAILED
    assert store.committed == {"failure_code": "CONTENT_REJECTED", "attempts": 1}
    assert queue.events[1][0] == "complete"


def test_worker_logs_only_safe_schema_diagnostic_without_changing_retry_contract(
    caplog,
) -> None:
    module = _module()
    queue = ScriptedQueue(claimed_job(attempt=1))
    store = ScriptedStore(module)
    failure = StorytellerFailure(
        "SCHEMA_INVALID",
        diagnostic_code="round_input_keys",
    )
    worker = module.StoryResolutionWorker(
        queue,
        store,
        Narrator(failure),
        max_attempts=2,
    )

    with caplog.at_level(logging.WARNING, logger="co_story.storyteller_schema"):
        worker.process("job-1", "worker-1")

    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "co_story.storyteller_schema"
    ]
    assert events == [
        {
            "operation": "resolve-round",
            "failure_code": "SCHEMA_INVALID",
            "diagnostic_code": "round_input_keys",
        }
    ]
    assert queue.events == ["claim", ("fail", "SCHEMA_INVALID")]
    assert store.events == ["inbox"]


@pytest.mark.parametrize(
    ("failure_code", "diagnostic_code"),
    [
        ("SCHEMA_INVALID", "raw model response"),
        ("TIMEOUT", "round_input_keys"),
    ],
)
def test_storyteller_failure_rejects_unallowlisted_or_unrelated_diagnostics(
    failure_code: str,
    diagnostic_code: str,
) -> None:
    with pytest.raises(ValueError, match="diagnostic_code"):
        StorytellerFailure(failure_code, diagnostic_code=diagnostic_code)
