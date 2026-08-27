from pathlib import Path


ROOT = Path(__file__).parents[1]
MIGRATION = ROOT / "migrations" / "003_create_story_resolution_results.sql"


def _sql():
    assert MIGRATION.is_file(), "003 story resolution migration 尚未建立"
    return " ".join(MIGRATION.read_text(encoding="utf-8").lower().split())


def test_003_is_append_only_and_defines_inbox_outbox_identity() -> None:
    sql = _sql()

    assert (ROOT / "migrations" / "001_create_rooms.sql").is_file()
    assert (ROOT / "migrations" / "002_create_story_jobs.sql").is_file()
    assert "create table story_result_inbox" in sql
    assert "job_id text primary key" in sql
    assert "references story_jobs" in sql
    assert "result_fingerprint" in sql
    assert "result jsonb not null" in sql
    assert "outcome" in sql
    assert "create table story_completion_outbox" in sql
    assert "ownership_token text not null" in sql
    assert "completion_payload jsonb not null" in sql


def test_003_constrains_utc_lifecycle_and_state_shape() -> None:
    sql = _sql()

    assert "created_at timestamptz not null" in sql
    assert "updated_at timestamptz not null" in sql
    assert "dispatched_at timestamptz" in sql
    assert "story_result_inbox_state_shape" in sql
    assert "applied" in sql
    assert "stale" in sql
    assert "failed" in sql
    assert "room_version_after is null" in sql
    assert "room_version_after is not null" in sql
    assert "check (result_fingerprint ~ '^[0-9a-f]{64}$')" in sql
