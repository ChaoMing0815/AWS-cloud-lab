from pathlib import Path


MIGRATION = Path(__file__).parents[1] / "migrations" / "001_create_rooms.sql"


def test_initial_migration_defines_versioned_room_aggregate_schema() -> None:
    assert MIGRATION.exists(), "PostgreSQL 初始 migration 尚未建立"

    sql = MIGRATION.read_text(encoding="utf-8").lower()

    assert "create table if not exists schema_migrations" in sql
    assert "create table if not exists rooms" in sql
    assert "room_code text not null unique" in sql
    assert "version integer not null" in sql
    assert "payload jsonb not null" in sql
    assert "created_at timestamptz not null" in sql
    assert "updated_at timestamptz not null" in sql
