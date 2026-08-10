import importlib
import importlib.util
import os
from pathlib import Path

import psycopg
import pytest


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


@pytest.mark.skipif(
    "CO_STORY_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定專題 PostgreSQL 測試資料庫",
)
def test_migration_runner_applies_empty_schema_idempotently() -> None:
    dsn = os.environ["CO_STORY_TEST_DATABASE_URL"]
    with psycopg.connect(dsn) as connection:
        connection.execute("DROP TABLE IF EXISTS rooms")
        connection.execute("DROP TABLE IF EXISTS schema_migrations")

    spec = importlib.util.find_spec("app.adapters.postgres_migrations")
    assert spec is not None, "PostgreSQL migration runner 尚未建立"

    module = importlib.import_module("app.adapters.postgres_migrations")
    module.apply_migrations(dsn)
    module.apply_migrations(dsn)

    with psycopg.connect(dsn) as connection:
        room_table = connection.execute("SELECT to_regclass('public.rooms')").fetchone()
        applied = connection.execute(
            "SELECT count(*) FROM schema_migrations WHERE version = %s",
            ("001_create_rooms",),
        ).fetchone()

    assert room_table == ("rooms",)
    assert applied == (1,)
