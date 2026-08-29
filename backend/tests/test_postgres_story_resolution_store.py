import importlib
import importlib.util
import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest

from app.adapters.postgres_room_repository import _room_payload
from app.application.story_jobs import create_story_job
from app.domain.story_jobs import StoryJobOperation, StoryJobStatus
from app.domain.story_resolution import StoryResolutionOutcome, StoryResolutionOwnershipConflict
from test_story_resolution_domain import resolution_room


NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


class MutableClock:
    def __init__(self):
        self.current = NOW

    def now(self):
        return self.current

    def advance(self, duration):
        self.current += duration


class Result:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None


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
        expected, rows = self.script.pop(0)
        assert expected in normalized
        return Result(rows)


def _module():
    spec = importlib.util.find_spec("app.adapters.postgres_story_resolution_store")
    assert spec is not None, "PostgreSQL story resolution coordinator 尚未建立"
    return importlib.import_module("app.adapters.postgres_story_resolution_store")


def _job_row(job):
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


def _claimed_job(*, token="token-1", lease_expires_at=None):
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
        lease_expires_at=lease_expires_at or NOW + timedelta(seconds=30),
        attempt_count=1,
    )


def _store(monkeypatch, connection, *, fault_hook=None):
    module = _module()
    monkeypatch.setattr(
        module,
        "psycopg",
        SimpleNamespace(connect=lambda dsn: connection),
    )
    return module.PostgresStoryResolutionStore(
        "postgresql://test/ignored",
        clock=MutableClock(),
        job_id_factory=lambda: "job-1",
        entry_id_factory=iter(["entry-result", "entry-ending"]).__next__,
        fault_hook=fault_hook,
    )


def test_postgres_coordinator_source_guards_atomic_producer_and_result_transactions() -> None:
    module = _module()
    source = Path(module.__file__).read_text(encoding="utf-8").lower()

    assert "for update" in source
    assert "insert into story_jobs" in source
    assert "insert into story_result_inbox" in source
    assert "insert into story_completion_outbox" in source
    assert "ownership_token" in source
    assert "lease_expires_at" in source
    assert "result_fingerprint" in source
    assert "room.version != job.room_version" in source
    assert source.index("insert into story_result_inbox") < source.index("mark_completion_dispatched")


def test_producer_fault_escapes_same_transaction_after_job_insert(monkeypatch) -> None:
    room = resolution_room()
    connection = ScriptedConnection(
        [
            ("from story_jobs", []),
            ("select payload from rooms", [(_room_payload(room),)]),
            ("insert into story_jobs", []),
        ]
    )

    def fail(point):
        if point == "after_job_insert":
            raise RuntimeError("injected producer rollback")

    store = _store(monkeypatch, connection, fault_hook=fail)

    with pytest.raises(RuntimeError, match="producer rollback"):
        store.begin_resolution("room-1", 2, 7, True)

    assert isinstance(connection.exit_error, RuntimeError)
    assert any("insert into story_jobs" in sql for sql, _ in connection.statements)
    assert not any("insert into rooms" in sql for sql, _ in connection.statements)


def test_producer_inserts_dispatch_outbox_before_room_commit(monkeypatch) -> None:
    room = resolution_room()
    connection = ScriptedConnection(
        [
            ("from story_jobs", []),
            ("select payload from rooms", [(_room_payload(room),)]),
            ("insert into story_jobs", []),
            ("insert into story_job_dispatch_outbox", []),
            ("insert into rooms", []),
        ]
    )
    store = _store(monkeypatch, connection)

    job = store.begin_resolution("room-1", 2, 7, True)

    statements = [sql for sql, _ in connection.statements]
    dispatch_sql = next(sql for sql in statements if "insert into story_job_dispatch_outbox" in sql)
    assert "jsonb_build_object" in dispatch_sql
    assert statements.index(dispatch_sql) < statements.index(
        next(sql for sql in statements if "insert into rooms" in sql)
    )


def test_result_commit_orders_room_inbox_and_outbox_in_one_transaction(monkeypatch) -> None:
    room = resolution_room(status="RESOLVING", version=8)
    room.dice_results[0].spark_decision = "DECLINE"
    job = _claimed_job()
    connection = ScriptedConnection(
        [
            ("from story_jobs", [_job_row(job)]),
            ("from story_result_inbox", []),
            ("select payload from rooms", [(_room_payload(room),)]),
            ("insert into rooms", []),
            ("insert into story_result_inbox", []),
            ("insert into story_completion_outbox", []),
        ]
    )
    store = _store(monkeypatch, connection)

    receipt = store.commit_result(job, {"narration": "canonical", "attempts": 1})

    assert receipt.outcome is StoryResolutionOutcome.APPLIED
    statements = [sql for sql, _ in connection.statements]
    assert statements.index(next(sql for sql in statements if "insert into rooms" in sql)) < statements.index(
        next(sql for sql in statements if "insert into story_result_inbox" in sql)
    )
    assert statements.index(next(sql for sql in statements if "insert into story_result_inbox" in sql)) < statements.index(
        next(sql for sql in statements if "insert into story_completion_outbox" in sql)
    )
    assert connection.exit_error is None


def test_result_fault_after_inbox_escapes_for_transaction_rollback(monkeypatch) -> None:
    room = resolution_room(status="RESOLVING", version=8)
    room.dice_results[0].spark_decision = "DECLINE"
    job = _claimed_job()
    connection = ScriptedConnection(
        [
            ("from story_jobs", [_job_row(job)]),
            ("from story_result_inbox", []),
            ("select payload from rooms", [(_room_payload(room),)]),
            ("insert into rooms", []),
            ("insert into story_result_inbox", []),
        ]
    )

    def fail(point):
        if point == "after_inbox_insert":
            raise RuntimeError("injected result rollback")

    store = _store(monkeypatch, connection, fault_hook=fail)

    with pytest.raises(RuntimeError, match="result rollback"):
        store.commit_result(job, {"narration": "rollback", "attempts": 1})

    assert isinstance(connection.exit_error, RuntimeError)
    assert not any("insert into story_completion_outbox" in sql for sql, _ in connection.statements)


@pytest.mark.parametrize(
    ("database_token", "lease_expiry"),
    [("new-token", NOW + timedelta(seconds=30)), ("token-1", NOW)],
)
def test_result_transaction_rejects_stale_or_expired_fencing_token(
    monkeypatch, database_token, lease_expiry
) -> None:
    supplied = _claimed_job()
    database_job = replace(supplied, ownership_token=database_token, lease_expires_at=lease_expiry)
    connection = ScriptedConnection([("from story_jobs", [_job_row(database_job)])])
    store = _store(monkeypatch, connection)

    with pytest.raises(StoryResolutionOwnershipConflict):
        store.commit_result(supplied, {"narration": "must reject", "attempts": 1})

    assert len(connection.statements) == 1


def test_result_transaction_rejects_tampered_claim_coordinates(monkeypatch) -> None:
    database_job = _claimed_job()
    supplied = replace(database_job, room_id="other-room", room_version=99)
    connection = ScriptedConnection([("from story_jobs", [_job_row(database_job)])])
    store = _store(monkeypatch, connection)

    with pytest.raises(StoryResolutionOwnershipConflict):
        store.commit_result(supplied, {"narration": "must reject", "attempts": 1})

    assert len(connection.statements) == 1


def test_stale_room_writes_terminal_receipt_without_room_update(monkeypatch) -> None:
    room = resolution_room(status="RESOLVING", version=9)
    job = _claimed_job()
    connection = ScriptedConnection(
        [
            ("from story_jobs", [_job_row(job)]),
            ("from story_result_inbox", []),
            ("select payload from rooms", [(_room_payload(room),)]),
            ("insert into story_result_inbox", []),
            ("insert into story_completion_outbox", []),
        ]
    )
    store = _store(monkeypatch, connection)

    receipt = store.commit_result(job, {"narration": "stale", "attempts": 1})

    assert receipt.outcome is StoryResolutionOutcome.STALE
    assert receipt.room_version_after is None
    assert not any("insert into rooms" in sql for sql, _ in connection.statements)
    inbox_params = next(params for sql, params in connection.statements if "insert into story_result_inbox" in sql)
    assert "stale" in inbox_params


@pytest.mark.skipif(
    "CO_STORY_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定專題 PostgreSQL 測試資料庫",
)
def test_result_inbox_survives_restart_and_reclaim_only_replays_completion() -> None:
    dsn = os.environ["CO_STORY_TEST_DATABASE_URL"]
    migrations = importlib.import_module("app.adapters.postgres_migrations")
    room_repository_module = importlib.import_module("app.adapters.postgres_room_repository")
    queue_module = importlib.import_module("app.adapters.postgres_story_job_queue")
    module = _module()
    clock = MutableClock()
    migrations.apply_migrations(dsn)
    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM story_completion_outbox")
        connection.execute("DELETE FROM story_result_inbox")
        connection.execute("DELETE FROM story_jobs")
        connection.execute("DELETE FROM rooms WHERE id = %s", ("room-1",))
    repository = room_repository_module.PostgresRoomRepository(dsn)
    repository.save(resolution_room())

    producer = module.PostgresStoryResolutionStore(
        dsn,
        clock=clock,
        job_id_factory=lambda: "job-1",
        entry_id_factory=lambda: "entry-result",
    )
    job = producer.begin_resolution("room-1", 2, 7, True)
    first_queue = queue_module.PostgresStoryJobQueue(
        dsn,
        clock=clock,
        lease_duration=timedelta(seconds=30),
        max_attempts=3,
        ownership_token_factory=lambda: "token-1",
    )
    first_claim = first_queue.claim(job.job_id, "worker-1")
    first_data = module.PostgresStoryResolutionStore(
        dsn,
        clock=clock,
        entry_id_factory=lambda: "entry-result",
    )
    receipt = first_data.commit_result(
        first_claim,
        {"narration": "durable canonical result", "attempts": 1},
    )
    room_after_commit = repository.get("room-1")

    clock.advance(timedelta(seconds=30))
    restarted_queue = queue_module.PostgresStoryJobQueue(
        dsn,
        clock=clock,
        lease_duration=timedelta(seconds=30),
        max_attempts=3,
        ownership_token_factory=lambda: "token-2",
    )
    reclaimed = restarted_queue.claim(job.job_id, "worker-2")
    restarted_data = module.PostgresStoryResolutionStore(dsn, clock=clock)
    replay = restarted_data.result_for_claim(reclaimed)
    assert replay == receipt
    restarted_queue.complete(job.job_id, "token-2", replay.completion_result)
    restarted_data.mark_completion_dispatched(job.job_id, "token-2")

    assert repository.get("room-1") == room_after_commit
