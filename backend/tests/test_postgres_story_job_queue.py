from __future__ import annotations

import importlib
import importlib.util
import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest

from app.application.story_jobs import create_story_job
from app.domain.story_jobs import (
    StoryJobConflict,
    StoryJobOperation,
    StoryJobOwnershipConflict,
    StoryJobStateConflict,
    StoryJobStatus,
)


NOW = datetime(2026, 8, 27, 9, 0, tzinfo=timezone.utc)


class MutableClock:
    def __init__(self) -> None:
        self.current = NOW

    def now(self) -> datetime:
        return self.current

    def advance(self, duration: timedelta) -> None:
        self.current += duration


class Result:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class ScriptedConnection:
    def __init__(self, script):
        self.script = list(script)
        self.statements = []
        self.exit_error = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.exit_error = exc
        return False

    def execute(self, sql, params=None):
        normalized = " ".join(sql.lower().split())
        self.statements.append((normalized, params))
        assert self.script, f"unexpected SQL: {normalized}"
        expected, outcome = self.script.pop(0)
        assert expected in normalized
        if isinstance(outcome, Exception):
            raise outcome
        return Result(outcome)


def _module():
    spec = importlib.util.find_spec("app.adapters.postgres_story_job_queue")
    assert spec is not None, "PostgreSQL story-job queue adapter 尚未建立"
    return importlib.import_module("app.adapters.postgres_story_job_queue")


def _job(*, job_id="job-1", room_id="room-1", payload=None):
    return create_story_job(
        operation=StoryJobOperation.RESOLVE_ROUND,
        room_id=room_id,
        round_number=2,
        room_version=7,
        payload=payload or {"scene": {"text": "sealed snapshot"}},
        job_id=job_id,
    )


def _row(job):
    return (
        job.job_id,
        job.idempotency_key,
        job.operation.value,
        job.room_id,
        job.round_number,
        job.room_version,
        job.payload,
        job.status.value,
        job.claimed_by,
        job.ownership_token,
        job.lease_expires_at,
        job.attempt_count,
        job.result,
        job.terminal_error,
    )


def _queue(monkeypatch, connection, *, max_attempts=3, tokens=("token-1", "token-2")):
    module = _module()
    token_iter = iter(tokens)
    monkeypatch.setattr(
        module,
        "psycopg",
        SimpleNamespace(connect=lambda dsn: connection),
    )
    clock = MutableClock()
    queue = module.PostgresStoryJobQueue(
        "postgresql://test/ignored",
        clock=clock,
        lease_duration=timedelta(seconds=30),
        max_attempts=max_attempts,
        ownership_token_factory=lambda: next(token_iter),
    )
    return queue, clock


def test_postgres_adapter_implements_existing_port_without_connecting() -> None:
    module = _module()
    ports = importlib.import_module("app.application.ports")

    queue = module.PostgresStoryJobQueue(
        "postgresql://test/ignored",
        clock=MutableClock(),
        lease_duration=timedelta(seconds=30),
        max_attempts=3,
    )

    assert isinstance(queue, ports.StoryJobQueue)


def test_enqueue_inserts_snapshot_and_duplicate_replay_is_stable(monkeypatch) -> None:
    job = _job()
    connection = ScriptedConnection(
        [
            ("insert into story_jobs", [_row(job)]),
            ("insert into story_jobs", []),
            ("for update", [_row(job)]),
        ]
    )
    queue, _ = _queue(monkeypatch, connection)

    assert queue.enqueue(job) == job
    returned = queue.enqueue(job)
    returned.payload["scene"]["text"] = "external mutation"

    assert job.payload == {"scene": {"text": "sealed snapshot"}}


def test_enqueue_rejects_cross_identity_collision(monkeypatch) -> None:
    first = _job(job_id="job-a")
    second = _job(job_id="job-b", room_id="room-b")
    cross = replace(first, idempotency_key=second.idempotency_key)
    connection = ScriptedConnection(
        [
            ("insert into story_jobs", []),
            ("for update", [_row(first), _row(second)]),
        ]
    )
    queue, _ = _queue(monkeypatch, connection)

    with pytest.raises(StoryJobConflict):
        queue.enqueue(cross)


def test_claim_uses_conditional_update_and_rejects_unexpired_takeover(monkeypatch) -> None:
    pending = _job()
    claimed = replace(
        pending,
        status=StoryJobStatus.CLAIMED,
        claimed_by="worker-a",
        ownership_token="token-1",
        lease_expires_at=NOW + timedelta(seconds=30),
        attempt_count=1,
    )
    connection = ScriptedConnection(
        [
            ("for update", [_row(pending)]),
            ("update story_jobs", [_row(claimed)]),
            ("for update", [_row(claimed)]),
        ]
    )
    queue, _ = _queue(monkeypatch, connection)

    assert queue.claim("job-1", "worker-a") == claimed
    with pytest.raises(StoryJobOwnershipConflict):
        queue.claim("job-1", "worker-b")
    update_sql = connection.statements[1][0]
    assert "status = 'pending'" in update_sql
    assert "lease_expires_at <=" in update_sql


def test_expired_claim_restarts_with_new_token_and_old_token_is_fenced(monkeypatch) -> None:
    expired = replace(
        _job(),
        status=StoryJobStatus.CLAIMED,
        claimed_by="worker-a",
        ownership_token="old-token",
        lease_expires_at=NOW,
        attempt_count=1,
    )
    reclaimed = replace(
        expired,
        claimed_by="worker-b",
        ownership_token="token-1",
        lease_expires_at=NOW + timedelta(seconds=30),
        attempt_count=2,
    )
    connection = ScriptedConnection(
        [
            ("for update", [_row(expired)]),
            ("update story_jobs", [_row(reclaimed)]),
            ("for update", [_row(reclaimed)]),
        ]
    )
    queue, _ = _queue(monkeypatch, connection)

    assert queue.claim("job-1", "worker-b") == reclaimed
    with pytest.raises(StoryJobOwnershipConflict):
        queue.complete("job-1", "old-token", {"narration": "stale"})


def test_complete_is_transactional_and_terminal_replay_is_fail_closed(monkeypatch) -> None:
    claimed = replace(
        _job(),
        status=StoryJobStatus.CLAIMED,
        claimed_by="worker-a",
        ownership_token="token-1",
        lease_expires_at=NOW + timedelta(seconds=30),
        attempt_count=1,
    )
    result = {"narration": "完成"}
    completed = replace(
        claimed,
        status=StoryJobStatus.COMPLETED,
        lease_expires_at=None,
        result=result,
    )
    connection = ScriptedConnection(
        [
            ("for update", [_row(claimed)]),
            ("update story_jobs", [_row(completed)]),
            ("for update", [_row(completed)]),
            ("for update", [_row(completed)]),
        ]
    )
    queue, _ = _queue(monkeypatch, connection)

    assert queue.complete("job-1", "token-1", result) == completed
    assert queue.complete("job-1", "token-1", result) == completed
    with pytest.raises(StoryJobConflict):
        queue.complete("job-1", "token-1", {"narration": "changed"})


def test_fail_requeues_then_durable_dead_letters_at_max_attempts(monkeypatch) -> None:
    claimed = replace(
        _job(),
        status=StoryJobStatus.CLAIMED,
        claimed_by="worker-a",
        ownership_token="token-1",
        lease_expires_at=NOW + timedelta(seconds=30),
        attempt_count=1,
    )
    pending = replace(
        claimed,
        status=StoryJobStatus.PENDING,
        claimed_by=None,
        ownership_token=None,
        lease_expires_at=None,
    )
    final_claim = replace(
        claimed,
        ownership_token="token-2",
        attempt_count=2,
    )
    terminal = replace(
        final_claim,
        status=StoryJobStatus.DEAD_LETTERED,
        claimed_by=None,
        ownership_token=None,
        lease_expires_at=None,
        terminal_error="TIMEOUT",
    )
    connection = ScriptedConnection(
        [
            ("for update", [_row(claimed)]),
            ("update story_jobs", [_row(pending)]),
            ("for update", [_row(final_claim)]),
            ("update story_jobs", [_row(terminal)]),
            ("for update", [_row(terminal)]),
        ]
    )
    queue, _ = _queue(monkeypatch, connection, max_attempts=2)

    assert queue.fail("job-1", "token-1", "TIMEOUT") == pending
    assert queue.fail("job-1", "token-2", "TIMEOUT") == terminal
    with pytest.raises(StoryJobStateConflict):
        queue.fail("job-1", "token-2", "TIMEOUT")


def test_database_error_escapes_transaction_for_rollback(monkeypatch) -> None:
    pending = _job()
    connection = ScriptedConnection(
        [
            ("for update", [_row(pending)]),
            ("update story_jobs", RuntimeError("injected write failure")),
        ]
    )
    queue, _ = _queue(monkeypatch, connection)

    with pytest.raises(RuntimeError, match="injected write failure"):
        queue.claim("job-1", "worker-a")

    assert isinstance(connection.exit_error, RuntimeError)


def test_adapter_source_contains_transactional_cas_guards() -> None:
    module = _module()
    source = Path(module.__file__).read_text(encoding="utf-8").lower()

    assert "for update" in source
    assert "on conflict do nothing" in source
    assert "ownership_token = %s" in source
    assert "lease_expires_at > %s" in source
    assert "returning" in source


@pytest.mark.skipif(
    "CO_STORY_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定專題 PostgreSQL 測試資料庫",
)
def test_postgres_queue_survives_adapter_restart_and_fences_expired_owner() -> None:
    dsn = os.environ["CO_STORY_TEST_DATABASE_URL"]
    migrations = importlib.import_module("app.adapters.postgres_migrations")
    module = _module()
    clock = MutableClock()
    migrations.apply_migrations(dsn)
    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM story_jobs")

    first = module.PostgresStoryJobQueue(
        dsn,
        clock=clock,
        lease_duration=timedelta(seconds=30),
        max_attempts=2,
        ownership_token_factory=lambda: "restart-token-1",
    )
    first.enqueue(_job())
    claimed = first.claim("job-1", "worker-a")

    clock.advance(timedelta(seconds=30))
    restarted = module.PostgresStoryJobQueue(
        dsn,
        clock=clock,
        lease_duration=timedelta(seconds=30),
        max_attempts=2,
        ownership_token_factory=lambda: "restart-token-2",
    )
    reclaimed = restarted.claim("job-1", "worker-b")

    assert reclaimed.attempt_count == 2
    assert reclaimed.ownership_token != claimed.ownership_token
    with pytest.raises(StoryJobOwnershipConflict):
        restarted.complete("job-1", claimed.ownership_token, {"narration": "stale"})
    completed = restarted.complete(
        "job-1", reclaimed.ownership_token, {"narration": "durable"}
    )
    assert completed.status is StoryJobStatus.COMPLETED
