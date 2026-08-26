from __future__ import annotations

import importlib
import importlib.util
from dataclasses import replace
from datetime import datetime, timedelta, timezone


def _contracts():
    required = (
        "app.domain.story_jobs",
        "app.application.story_jobs",
        "app.adapters.memory_story_job_queue",
    )
    for module_name in required:
        assert importlib.util.find_spec(module_name) is not None, f"{module_name} 尚未建立"
    domain = importlib.import_module("app.domain.story_jobs")
    application = importlib.import_module("app.application.story_jobs")
    adapter = importlib.import_module("app.adapters.memory_story_job_queue")
    ports = importlib.import_module("app.application.ports")
    return domain, application, adapter, ports


def _job(
    application,
    domain,
    *,
    job_id="job-1",
    room_id="room-1",
    round_number=2,
    room_version=7,
    payload=None,
):
    return application.create_story_job(
        operation=domain.StoryJobOperation.RESOLVE_ROUND,
        room_id=room_id,
        round_number=round_number,
        room_version=room_version,
        payload=payload or {"scene": "sealed snapshot"},
        job_id=job_id,
    )


class MutableClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 8, 26, 9, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.current

    def advance(self, duration: timedelta) -> None:
        self.current += duration


def _queue(adapter, *, max_attempts=3):
    clock = MutableClock()
    tokens = iter(("token-claim-1", "token-claim-2", "token-claim-3"))
    queue = adapter.MemoryStoryJobQueue(
        clock=clock,
        lease_duration=timedelta(seconds=30),
        max_attempts=max_attempts,
        ownership_token_factory=lambda: next(tokens),
    )
    return queue, clock


def test_memory_queue_implements_port_and_deduplicates_identical_enqueue() -> None:
    domain, application, adapter, ports = _contracts()
    queue, _ = _queue(adapter)
    job = _job(application, domain)

    first = queue.enqueue(job)
    replay = queue.enqueue(job)

    assert isinstance(queue, ports.StoryJobQueue)
    assert first == replay == job
    assert queue.job_count == 1


def test_enqueue_rejects_same_idempotency_key_with_different_content() -> None:
    domain, application, adapter, _ = _contracts()
    queue, _ = _queue(adapter)
    queue.enqueue(_job(application, domain))

    try:
        queue.enqueue(_job(application, domain, job_id="job-conflict", payload={"scene": "changed"}))
    except domain.StoryJobConflict:
        pass
    else:
        raise AssertionError("同一 idempotency key 的不同內容應被拒絕")


def test_enqueue_rejects_cross_identity_collision_between_two_existing_jobs() -> None:
    domain, application, adapter, _ = _contracts()
    queue, _ = _queue(adapter)
    first = _job(application, domain, job_id="job-a")
    second = _job(
        application,
        domain,
        job_id="job-b",
        room_id="room-2",
    )
    queue.enqueue(first)
    queue.enqueue(second)
    cross_collision = replace(first, idempotency_key=second.idempotency_key)

    try:
        queue.enqueue(cross_collision)
    except domain.StoryJobConflict:
        pass
    else:
        raise AssertionError("job_id 與 idempotency_key 指向不同既有 job 時必須拒絕")


def test_claim_is_idempotent_for_owner_and_rejects_competing_worker() -> None:
    domain, application, adapter, _ = _contracts()
    queue, _ = _queue(adapter)
    queue.enqueue(_job(application, domain))

    claimed = queue.claim("job-1", "worker-a")
    replay = queue.claim("job-1", "worker-a")

    assert claimed.status is domain.StoryJobStatus.CLAIMED
    assert claimed.claimed_by == "worker-a"
    assert claimed.ownership_token == "token-claim-1"
    assert claimed.lease_expires_at == datetime(2026, 8, 26, 9, 0, 30, tzinfo=timezone.utc)
    assert claimed.attempt_count == 1
    assert replay == claimed
    try:
        queue.claim("job-1", "worker-b")
    except domain.StoryJobOwnershipConflict:
        pass
    else:
        raise AssertionError("其他 worker 不可接管已 claim job")


def test_complete_is_idempotent_only_for_same_owner_and_result() -> None:
    domain, application, adapter, _ = _contracts()
    queue, _ = _queue(adapter)
    queue.enqueue(_job(application, domain))
    claimed = queue.claim("job-1", "worker-a")

    completed = queue.complete(
        "job-1", claimed.ownership_token, {"narration": "門鎖發出喀聲。"}
    )
    replay = queue.complete(
        "job-1", claimed.ownership_token, {"narration": "門鎖發出喀聲。"}
    )

    assert completed.status is domain.StoryJobStatus.COMPLETED
    assert replay == completed
    for ownership_token, result in (
        ("stale-or-foreign-token", {"narration": "門鎖發出喀聲。"}),
        (claimed.ownership_token, {"narration": "不同結果"}),
    ):
        try:
            queue.complete("job-1", ownership_token, result)
        except domain.StoryJobConflict:
            pass
        else:
            raise AssertionError("completion replay 不可改變 owner 或 result")


def test_unknown_job_and_completed_reclaim_are_rejected() -> None:
    domain, application, adapter, _ = _contracts()
    queue, _ = _queue(adapter)

    try:
        queue.claim("missing", "worker-a")
    except domain.StoryJobNotFound:
        pass
    else:
        raise AssertionError("unknown job 應回報 not found")

    queue.enqueue(_job(application, domain))
    claimed = queue.claim("job-1", "worker-a")
    queue.complete("job-1", claimed.ownership_token, {"narration": "完成"})
    try:
        queue.claim("job-1", "worker-a")
    except domain.StoryJobStateConflict:
        pass
    else:
        raise AssertionError("completed job 不可重新 claim")


def test_expired_lease_is_reclaimed_with_new_fencing_token() -> None:
    domain, application, adapter, _ = _contracts()
    queue, clock = _queue(adapter)
    queue.enqueue(_job(application, domain))
    first = queue.claim("job-1", "worker-a")

    clock.advance(timedelta(seconds=30))
    second = queue.claim("job-1", "worker-b")

    assert second.claimed_by == "worker-b"
    assert second.ownership_token == "token-claim-2"
    assert second.ownership_token != first.ownership_token
    assert second.attempt_count == 2
    try:
        queue.complete("job-1", first.ownership_token, {"narration": "stale"})
    except domain.StoryJobOwnershipConflict:
        pass
    else:
        raise AssertionError("過期 lease 的舊 fencing token 不可完成 job")


def test_expired_token_cannot_complete_before_another_worker_reclaims() -> None:
    domain, application, adapter, _ = _contracts()
    queue, clock = _queue(adapter)
    queue.enqueue(_job(application, domain))
    claimed = queue.claim("job-1", "worker-a")

    clock.advance(timedelta(seconds=30))
    try:
        queue.complete("job-1", claimed.ownership_token, {"narration": "too late"})
    except domain.StoryJobOwnershipConflict:
        pass
    else:
        raise AssertionError("到期 fencing token 即使尚未被接管也不可完成 job")


def test_expired_lease_dead_letters_when_max_attempts_are_exhausted() -> None:
    domain, application, adapter, _ = _contracts()
    queue, clock = _queue(adapter, max_attempts=1)
    queue.enqueue(_job(application, domain))
    queue.claim("job-1", "worker-a")

    clock.advance(timedelta(seconds=30))
    terminal = queue.claim("job-1", "worker-b")

    assert terminal.status is domain.StoryJobStatus.DEAD_LETTERED
    assert terminal.attempt_count == 1
    assert terminal.terminal_error == "LEASE_EXPIRED"


def test_explicit_fail_retries_then_dead_letters_at_max_attempts() -> None:
    domain, application, adapter, _ = _contracts()
    queue, _ = _queue(adapter, max_attempts=2)
    queue.enqueue(_job(application, domain))

    first = queue.claim("job-1", "worker-a")
    pending = queue.fail("job-1", first.ownership_token, "TRANSIENT_SERVICE_ERROR")
    assert pending.status is domain.StoryJobStatus.PENDING
    assert pending.attempt_count == 1

    second = queue.claim("job-1", "worker-b")
    terminal = queue.fail("job-1", second.ownership_token, "TRANSIENT_SERVICE_ERROR")
    assert terminal.status is domain.StoryJobStatus.DEAD_LETTERED
    assert terminal.attempt_count == 2
    assert terminal.terminal_error == "TRANSIENT_SERVICE_ERROR"
    try:
        queue.claim("job-1", "worker-c")
    except domain.StoryJobStateConflict:
        pass
    else:
        raise AssertionError("dead-lettered job 不可無限重試")


def test_nested_payload_mutation_does_not_change_enqueued_snapshot() -> None:
    domain, application, adapter, _ = _contracts()
    queue, _ = _queue(adapter)
    job = _job(
        application,
        domain,
        payload={"actions": [{"details": {"text": "原始行動"}}]},
    )

    returned = queue.enqueue(job)
    returned.payload["actions"][0]["details"]["text"] = "外部竄改"

    replay = queue.enqueue(job)
    assert replay.payload == {"actions": [{"details": {"text": "原始行動"}}]}
