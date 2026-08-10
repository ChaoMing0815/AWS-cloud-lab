from pathlib import Path

import psycopg


MIGRATIONS_ROOT = Path(__file__).resolve().parents[2] / "migrations"


def apply_migrations(dsn: str) -> None:
    migration = MIGRATIONS_ROOT / "001_create_rooms.sql"
    sql = migration.read_text(encoding="utf-8")
    with psycopg.connect(dsn) as connection:
        connection.execute(sql)
