from pathlib import Path


ROOT = Path(__file__).parents[1]
MIGRATION = ROOT / "migrations" / "002_create_story_jobs.sql"
INITIAL_MIGRATION = ROOT / "migrations" / "001_create_rooms.sql"


def _sql() -> str:
    assert MIGRATION.is_file(), "PostgreSQL story_jobs migration 尚未建立"
    return " ".join(MIGRATION.read_text(encoding="utf-8").lower().split())


def test_story_job_migration_is_append_only_and_defines_durable_identity() -> None:
    sql = _sql()

    assert INITIAL_MIGRATION.is_file()
    assert "create table story_jobs" in sql
    assert "job_id text primary key" in sql
    assert "idempotency_key text not null unique" in sql
    assert "operation text not null" in sql
    assert "room_id text not null" in sql
    assert "round_number integer not null" in sql
    assert "room_version integer not null" in sql
    assert "payload jsonb not null" in sql


def test_story_job_migration_constrains_lifecycle_and_utc_timestamps() -> None:
    sql = _sql()

    for column in (
        "status text not null",
        "attempt_count integer not null",
        "claimed_by text",
        "ownership_token text",
        "lease_expires_at timestamptz",
        "result jsonb",
        "terminal_error text",
        "created_at timestamptz not null",
        "updated_at timestamptz not null",
        "completed_at timestamptz",
        "dead_lettered_at timestamptz",
    ):
        assert column in sql
    assert "check (round_number > 0)" in sql
    assert "check (room_version >= 0)" in sql
    assert "check (attempt_count >= 0)" in sql
    assert "pending" in sql
    assert "claimed" in sql
    assert "completed" in sql
    assert "dead-lettered" in sql
    assert "create unique index" in sql
    assert "ownership_token" in sql


def test_story_job_migration_fail_closes_invalid_state_shapes() -> None:
    sql = _sql()

    assert "story_jobs_state_shape" in sql
    assert "status = 'pending'" in sql
    assert "status = 'claimed'" in sql
    assert "status = 'completed'" in sql
    assert "status = 'dead-lettered'" in sql
    assert "lease_expires_at is not null" in sql
    assert "result is not null" in sql
    assert "terminal_error is not null" in sql
