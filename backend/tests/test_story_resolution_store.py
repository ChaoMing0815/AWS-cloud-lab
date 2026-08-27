from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib
import importlib.util

import pytest

from app.application.story_jobs import create_story_job
from app.domain.story_jobs import StoryJobOperation, StoryJobStatus
from test_story_resolution_domain import resolution_room


NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


class FixedClock:
    def now(self):
        return NOW


def _modules():
    adapter_spec = importlib.util.find_spec("app.adapters.memory_story_resolution_store")
    assert adapter_spec is not None, "memory story resolution transaction double 尚未建立"
    return (
        importlib.import_module("app.adapters.memory_story_resolution_store"),
        importlib.import_module("app.domain.story_resolution"),
    )


def _store(*, room=None, fault_hook=None):
    adapter, _ = _modules()
    return adapter.MemoryStoryResolutionStore(
        [room or resolution_room()],
        clock=FixedClock(),
        job_id_factory=lambda: "job-1",
        entry_id_factory=iter(["entry-result", "entry-ending"]).__next__,
        fault_hook=fault_hook,
    )


def _claimed_job(*, token="token-1", attempt=1, expires_at=None):
    pending = create_story_job(
        operation=StoryJobOperation.RESOLVE_ROUND,
        room_id="room-1",
        round_number=2,
        room_version=8,
        payload={"world": {"name": "霽霧之城"}},
        job_id="job-1",
    )
    return replace(
        pending,
        status=StoryJobStatus.CLAIMED,
        claimed_by="worker-1",
        ownership_token=token,
        lease_expires_at=expires_at or NOW + timedelta(seconds=30),
        attempt_count=attempt,
    )


def test_producer_atomically_transitions_room_and_returns_stable_replay() -> None:
    store = _store()

    job = store.begin_resolution(
        room_id="room-1",
        round_number=2,
        expected_version=7,
        skip_pending_spark=True,
    )
    replay = store.begin_resolution(
        room_id="room-1",
        round_number=2,
        expected_version=7,
        skip_pending_spark=True,
    )

    persisted = store.room("room-1")
    assert job == replay
    assert persisted.status == "RESOLVING"
    assert persisted.version == 8
    assert persisted.dice_results[0].spark_decision == "DECLINE"
    assert job.room_version == 8
    assert job.payload["producer"] == {"source_room_version": 7, "skip_pending_spark": True}


def test_producer_conflicting_replay_fails_closed() -> None:
    _, domain = _modules()
    store = _store()
    store.begin_resolution("room-1", 2, 7, True)

    with pytest.raises(domain.StoryResolutionConflict):
        store.begin_resolution("room-1", 2, 7, False)


def test_producer_fault_rolls_back_room_and_job_together() -> None:
    def fail(point):
        if point == "after_job_insert":
            raise RuntimeError("injected producer failure")

    store = _store(fault_hook=fail)
    before = store.room("room-1")

    with pytest.raises(RuntimeError, match="producer failure"):
        store.begin_resolution("room-1", 2, 7, True)

    assert store.room("room-1") == before
    assert store.job("job-1") is None


def test_result_applies_once_and_identical_replay_returns_receipt() -> None:
    _, domain = _modules()
    room = resolution_room(status="RESOLVING", version=8)
    room.dice_results[0].spark_decision = "DECLINE"
    store = _store(room=room)
    job = _claimed_job()
    result = {"narration": "燈塔亮起微光。", "attempts": 1}

    assert store.result_for_claim(job) is None
    receipt = store.commit_result(job, result)
    replay = store.commit_result(job, result)

    persisted = store.room("room-1")
    assert receipt == replay
    assert receipt.outcome is domain.StoryResolutionOutcome.APPLIED
    assert persisted.version == 9
    assert persisted.round_number == 3
    assert persisted.progress_points == 1
    assert persisted.danger_points == 1
    assert [entry.text for entry in persisted.entries].count("燈塔亮起微光。") == 1


def test_divergent_result_for_same_job_is_rejected() -> None:
    _, domain = _modules()
    room = resolution_room(status="RESOLVING", version=8)
    room.dice_results[0].spark_decision = "DECLINE"
    store = _store(room=room)
    job = _claimed_job()
    store.result_for_claim(job)
    store.commit_result(job, {"narration": "first", "attempts": 1})

    with pytest.raises(domain.StoryResolutionConflict):
        store.commit_result(job, {"narration": "changed", "attempts": 1})


def test_stale_room_creates_terminal_receipt_without_room_mutation() -> None:
    _, domain = _modules()
    room = resolution_room(status="RESOLVING", version=9)
    room.dice_results[0].spark_decision = "DECLINE"
    store = _store(room=room)
    job = _claimed_job()
    before = store.room("room-1")
    store.result_for_claim(job)

    receipt = store.commit_result(job, {"narration": "stale", "attempts": 1})

    assert receipt.outcome is domain.StoryResolutionOutcome.STALE
    assert receipt.room_version_after is None
    assert store.room("room-1") == before


def test_expired_and_reclaimed_tokens_fail_closed() -> None:
    _, domain = _modules()
    room = resolution_room(status="RESOLVING", version=8)
    store = _store(room=room)
    expired = _claimed_job(expires_at=NOW)

    with pytest.raises(domain.StoryResolutionOwnershipConflict):
        store.result_for_claim(expired)

    first = _claimed_job(token="old-token", attempt=1)
    reclaimed = _claimed_job(token="new-token", attempt=2)
    store.result_for_claim(first)
    store.result_for_claim(reclaimed)
    with pytest.raises(domain.StoryResolutionOwnershipConflict):
        store.commit_result(first, {"narration": "late", "attempts": 1})


def test_result_fault_rolls_back_room_inbox_and_outbox() -> None:
    calls = []

    def fail(point):
        calls.append(point)
        if point == "after_inbox_insert":
            raise RuntimeError("injected result failure")

    room = resolution_room(status="RESOLVING", version=8)
    room.dice_results[0].spark_decision = "DECLINE"
    store = _store(room=room, fault_hook=fail)
    job = _claimed_job()
    before = store.room("room-1")
    store.result_for_claim(job)

    with pytest.raises(RuntimeError, match="result failure"):
        store.commit_result(job, {"narration": "rollback", "attempts": 1})

    assert "after_inbox_insert" in calls
    assert store.room("room-1") == before
    assert store.receipt("job-1") is None
    assert store.outbox("job-1") is None
