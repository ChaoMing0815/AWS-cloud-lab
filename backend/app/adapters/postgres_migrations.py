import re
from pathlib import Path

import psycopg


MIGRATIONS_ROOT = Path(__file__).resolve().parents[2] / "migrations"
_MIGRATION_FILENAME = re.compile(r"^(?P<prefix>\d{3})_[A-Za-z0-9][A-Za-z0-9_]*\.sql$")
_BOOTSTRAP_SCHEMA_MIGRATIONS = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
)
"""


def expected_migration_versions() -> tuple[str, ...]:
    """Return the ordered migration versions required by this release."""
    return tuple(version for version, _ in _discover_migrations())


def apply_migrations(dsn: str) -> None:
    migrations = _discover_migrations()
    with psycopg.connect(dsn) as connection:
        connection.execute(_BOOTSTRAP_SCHEMA_MIGRATIONS)
        applied_versions = {
            row[0]
            for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
        }
        for version, migration in migrations:
            if version in applied_versions:
                continue
            with connection.transaction():
                connection.execute(migration.read_text(encoding="utf-8"))
                connection.execute(
                    """
                    INSERT INTO schema_migrations (version)
                    VALUES (%s)
                    ON CONFLICT (version) DO NOTHING
                    """,
                    (version,),
                )
            applied_versions.add(version)


def _discover_migrations() -> list[tuple[str, Path]]:
    migrations: list[tuple[str, Path]] = []
    numeric_prefixes: set[str] = set()
    for path in MIGRATIONS_ROOT.iterdir():
        if not path.is_file() or path.suffix != ".sql":
            continue
        match = _MIGRATION_FILENAME.fullmatch(path.name)
        if match is None:
            raise ValueError(f"invalid migration filename: {path.name}")
        prefix = match.group("prefix")
        if prefix in numeric_prefixes:
            raise ValueError(f"duplicate migration version prefix: {prefix}")
        numeric_prefixes.add(prefix)
        migrations.append((path.stem, path))
    return sorted(migrations, key=lambda item: item[0])
