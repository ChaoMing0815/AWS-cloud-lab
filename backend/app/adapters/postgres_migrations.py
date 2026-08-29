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
_CANONICAL_INVENTORIES = (
    ("001_create_rooms",),
    ("001_create_rooms", "002_create_story_jobs"),
    (
        "001_create_rooms",
        "002_create_story_jobs",
        "003_create_story_resolution_results",
    ),
    (
        "001_create_rooms",
        "002_create_story_jobs",
        "003_create_story_resolution_results",
        "004_create_support_report_drafts",
    ),
    (
        "001_create_rooms",
        "002_create_story_jobs",
        "003_create_story_resolution_results",
        "004_create_support_report_drafts",
        "005_create_story_job_dispatch_outbox",
    ),
)


def validate_migration_inventory(inventory) -> tuple[str, ...]:
    """Accept only an exact, ordered prefix of the audited migration inventory."""
    values = tuple(inventory)
    if values not in _CANONICAL_INVENTORIES:
        raise ValueError("invalid migration inventory")
    return values


def expected_migration_versions() -> tuple[str, ...]:
    """Return the ordered migration versions required by this release."""
    return validate_migration_inventory(version for version, _ in _discover_migrations())


def apply_migrations(dsn: str) -> None:
    migrations = _discover_migrations()
    validate_migration_inventory(version for version, _ in migrations)
    with psycopg.connect(dsn) as connection:
        connection.execute(_BOOTSTRAP_SCHEMA_MIGRATIONS)
        applied_versions = tuple(
            row[0]
            for row in connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            ).fetchall()
        )
        if applied_versions:
            validate_migration_inventory(applied_versions)
        elif not migrations or migrations[0][0] != "001_create_rooms":
            raise ValueError("invalid migration inventory")
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
            applied_versions += (version,)


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
