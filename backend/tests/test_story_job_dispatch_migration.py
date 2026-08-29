from pathlib import Path


ROOT = Path(__file__).parents[1]
MIGRATION = ROOT / "migrations" / "005_create_story_job_dispatch_outbox.sql"


def test_dispatch_outbox_migration_is_append_only_and_replay_safe() -> None:
    assert MIGRATION.is_file(), "StoryJob dispatch outbox migration 尚未建立"
    sql = " ".join(MIGRATION.read_text(encoding="utf-8").lower().split())

    assert "create table story_job_dispatch_outbox" in sql
    assert "job_id text primary key references story_jobs" in sql
    assert "message_payload jsonb not null" in sql
    assert "status text not null" in sql
    assert "lease_token text" in sql
    assert "lease_expires_at timestamptz" in sql
    assert "attempt_count integer not null default 0" in sql
    assert "dispatched_at timestamptz" in sql
    assert "story_job_dispatch_outbox_state_shape" in sql
    assert "story_job_dispatch_outbox_claimable_idx" in sql
    assert "alter table story_jobs" not in sql
    assert "drop table" not in sql


def test_dispatch_outbox_payload_is_an_opaque_versioned_job_signal() -> None:
    sql = " ".join(MIGRATION.read_text(encoding="utf-8").lower().split())

    assert "jsonb_build_object('schema_version', 1, 'job_id', job_id)" in sql
    assert "(message_payload - 'schema_version' - 'job_id') = '{}'::jsonb" in sql
    assert "jsonb_object_length" not in sql
    assert "message_payload ->> 'schema_version' = '1'" in sql
    assert "message_payload ->> 'job_id' = job_id" in sql
    assert "jsonb_typeof(message_payload -> 'schema_version') = 'number'" in sql
    assert "jsonb_typeof(message_payload -> 'job_id') = 'string'" in sql
