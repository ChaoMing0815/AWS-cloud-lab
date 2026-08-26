from __future__ import annotations

import importlib
import importlib.util


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


def _job(application, domain, *, job_id="job-1", payload=None):
    return application.create_story_job(
        operation=domain.StoryJobOperation.RESOLVE_ROUND,
        room_id="room-1",
        round_number=2,
        room_version=7,
        payload=payload or {"scene": "sealed snapshot"},
        job_id=job_id,
    )


def test_memory_queue_implements_port_and_deduplicates_identical_enqueue() -> None:
    domain, application, adapter, ports = _contracts()
    queue = adapter.MemoryStoryJobQueue()
    job = _job(application, domain)

    first = queue.enqueue(job)
    replay = queue.enqueue(job)

    assert isinstance(queue, ports.StoryJobQueue)
    assert first == replay == job
    assert queue.job_count == 1


def test_enqueue_rejects_same_idempotency_key_with_different_content() -> None:
    domain, application, adapter, _ = _contracts()
    queue = adapter.MemoryStoryJobQueue()
    queue.enqueue(_job(application, domain))

    try:
        queue.enqueue(_job(application, domain, job_id="job-conflict", payload={"scene": "changed"}))
    except domain.StoryJobConflict:
        pass
    else:
        raise AssertionError("同一 idempotency key 的不同內容應被拒絕")


def test_claim_is_idempotent_for_owner_and_rejects_competing_worker() -> None:
    domain, application, adapter, _ = _contracts()
    queue = adapter.MemoryStoryJobQueue()
    queue.enqueue(_job(application, domain))

    claimed = queue.claim("job-1", "worker-a")
    replay = queue.claim("job-1", "worker-a")

    assert claimed.status is domain.StoryJobStatus.CLAIMED
    assert claimed.claimed_by == "worker-a"
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
    queue = adapter.MemoryStoryJobQueue()
    queue.enqueue(_job(application, domain))
    queue.claim("job-1", "worker-a")

    completed = queue.complete("job-1", "worker-a", {"narration": "門鎖發出喀聲。"})
    replay = queue.complete("job-1", "worker-a", {"narration": "門鎖發出喀聲。"})

    assert completed.status is domain.StoryJobStatus.COMPLETED
    assert replay == completed
    for worker_id, result in (
        ("worker-b", {"narration": "門鎖發出喀聲。"}),
        ("worker-a", {"narration": "不同結果"}),
    ):
        try:
            queue.complete("job-1", worker_id, result)
        except domain.StoryJobConflict:
            pass
        else:
            raise AssertionError("completion replay 不可改變 owner 或 result")


def test_unknown_job_and_completed_reclaim_are_rejected() -> None:
    domain, application, adapter, _ = _contracts()
    queue = adapter.MemoryStoryJobQueue()

    try:
        queue.claim("missing", "worker-a")
    except domain.StoryJobNotFound:
        pass
    else:
        raise AssertionError("unknown job 應回報 not found")

    queue.enqueue(_job(application, domain))
    queue.claim("job-1", "worker-a")
    queue.complete("job-1", "worker-a", {"narration": "完成"})
    try:
        queue.claim("job-1", "worker-a")
    except domain.StoryJobStateConflict:
        pass
    else:
        raise AssertionError("completed job 不可重新 claim")
