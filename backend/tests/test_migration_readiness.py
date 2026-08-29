import importlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


class _Result:
    def __init__(self, rows=()):
        self._rows = list(rows)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _Transaction:
    def __init__(self, connection):
        self._connection = connection

    def __enter__(self):
        self._connection.transaction_count += 1
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class _MigrationConnection:
    def __init__(self, applied_versions=()):
        self.applied_versions = list(applied_versions)
        self.statements = []
        self.transaction_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def transaction(self):
        return _Transaction(self)

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        normalized = " ".join(sql.lower().split())
        if "select version from schema_migrations" in normalized:
            assert "order by version" in normalized
            return _Result([(version,) for version in self.applied_versions])
        if "insert into schema_migrations" in normalized:
            self.applied_versions.append(params[0])
        return _Result()


def _migration_module():
    spec = importlib.util.find_spec("app.adapters.postgres_migrations")
    assert spec is not None, "PostgreSQL migration runner 尚未建立"
    return importlib.import_module("app.adapters.postgres_migrations")


def _write_migration(root, filename, marker):
    (root / filename).write_text(f"-- {marker}\nSELECT '{marker}';\n", encoding="utf-8")


def test_migration_runner_discovers_sorted_unapplied_files_and_records_each_version_atomically(
    tmp_path, monkeypatch
) -> None:
    _write_migration(tmp_path, "001_create_rooms.sql", "one")
    _write_migration(tmp_path, "002_create_story_jobs.sql", "two")
    connection = _MigrationConnection(applied_versions=("001_create_rooms",))
    module = _migration_module()
    monkeypatch.setattr(module, "MIGRATIONS_ROOT", tmp_path)
    monkeypatch.setattr(
        module,
        "psycopg",
        SimpleNamespace(connect=lambda dsn: connection),
    )

    module.apply_migrations("postgresql://test/ignored")
    module.apply_migrations("postgresql://test/ignored")

    executed_sql = [sql for sql, _ in connection.statements]
    assert connection.applied_versions == ["001_create_rooms", "002_create_story_jobs"]
    assert sum("-- two" in sql for sql in executed_sql) == 1
    assert not any("-- one" in sql for sql in executed_sql)
    version_inserts = [
        params
        for sql, params in connection.statements
        if "insert into schema_migrations" in sql.lower()
    ]
    assert version_inserts == [("002_create_story_jobs",)]
    assert connection.transaction_count == 1


@pytest.mark.parametrize(
    "filenames",
    [
        ("001_create_rooms.sql", "001_duplicate.sql"),
        ("001_create_rooms.sql", "not-a-migration.sql"),
        ("001_create_rooms.sql", "1_ambiguous_version.sql"),
        ("001_create_rooms.sql", "0001_overwide_version.sql"),
    ],
)
def test_migration_runner_rejects_duplicate_versions_and_invalid_filenames(
    tmp_path, monkeypatch, filenames
) -> None:
    for filename in filenames:
        _write_migration(tmp_path, filename, filename)
    module = _migration_module()
    monkeypatch.setattr(module, "MIGRATIONS_ROOT", tmp_path)
    monkeypatch.setattr(
        module,
        "psycopg",
        SimpleNamespace(connect=lambda dsn: _MigrationConnection()),
    )

    with pytest.raises(ValueError):
        module.apply_migrations("postgresql://test/ignored")


@pytest.mark.parametrize(
    "applied_inventory",
    (
        ("001_create_rooms", "999_unknown"),
        ("001_create_rooms", "003_create_story_resolution_results"),
        ("001_create_rooms", "001_create_rooms"),
        ("001_create_rooms.sql",),
    ),
)
def test_migration_runner_rejects_invalid_applied_inventory_before_migration_sql_or_insert(
    tmp_path, monkeypatch, applied_inventory
) -> None:
    _write_migration(tmp_path, "001_create_rooms.sql", "one")
    _write_migration(tmp_path, "002_create_story_jobs.sql", "two")
    connection = _MigrationConnection(applied_versions=applied_inventory)
    module = _migration_module()
    monkeypatch.setattr(module, "MIGRATIONS_ROOT", tmp_path)
    monkeypatch.setattr(module, "psycopg", SimpleNamespace(connect=lambda _dsn: connection))

    with pytest.raises(ValueError, match="migration inventory"):
        module.apply_migrations("postgresql://test/ignored")

    statements = [sql for sql, _params in connection.statements]
    assert not any("-- one" in sql or "-- two" in sql for sql in statements)
    assert not any("insert into schema_migrations" in sql.lower() for sql in statements)


@pytest.mark.parametrize(
    "inventory",
    (
        ("001_create_rooms",),
        ("001_create_rooms", "002_create_story_jobs"),
        ("001_create_rooms", "002_create_story_jobs", "003_create_story_resolution_results"),
        ("001_create_rooms", "002_create_story_jobs", "003_create_story_resolution_results", "004_create_support_report_drafts"),
        ("001_create_rooms", "002_create_story_jobs", "003_create_story_resolution_results", "004_create_support_report_drafts", "005_create_story_job_dispatch_outbox"),
    ),
)
def test_canonical_inventory_validator_accepts_only_complete_append_only_prefixes(inventory) -> None:
    module = _migration_module()

    assert module.validate_migration_inventory(inventory) == inventory


@pytest.mark.parametrize(
    "inventory",
    (
        (),
        ("002_create_story_jobs",),
        ("001_create_rooms", "003_create_story_resolution_results"),
        ("001_create_rooms", "002_create_story_jobs", "999_unknown"),
        ("001_create_rooms", "001_create_rooms"),
        ("001_create_rooms.sql",),
    ),
)
def test_canonical_inventory_validator_rejects_empty_gap_unknown_duplicate_and_malformed(inventory) -> None:
    module = _migration_module()

    with pytest.raises(ValueError, match="migration inventory"):
        module.validate_migration_inventory(inventory)


def test_migration_cli_requires_database_url_without_echoing_a_dsn() -> None:
    environment = dict(os.environ)
    environment.pop("DATABASE_URL", None)
    result = subprocess.run(
        [sys.executable, "-m", "app.commands.migrate"],
        cwd=Path(__file__).parents[1],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "DATABASE_URL" in result.stderr
    assert "postgresql://" not in result.stderr.lower()


def test_migration_cli_applies_configured_database_without_printing_dsn(
    monkeypatch, capsys
) -> None:
    spec = importlib.util.find_spec("app.commands.migrate")
    assert spec is not None, "獨立 migration CLI 尚未建立"
    module = importlib.import_module("app.commands.migrate")
    dsn = "postgresql://app:secret@db.example.test/co_story"
    calls = []
    monkeypatch.setenv("DATABASE_URL", dsn)
    monkeypatch.setattr(module, "apply_migrations", lambda value: calls.append(value))

    assert module.main() == 0
    captured = capsys.readouterr()
    assert calls == [dsn]
    assert dsn not in captured.out
    assert dsn not in captured.err


def test_create_app_does_not_apply_migrations_during_web_boot(monkeypatch) -> None:
    main = importlib.import_module("app.main")

    def must_not_run(*args, **kwargs):
        raise AssertionError("Web boot 不得自動套用 migration")

    monkeypatch.setattr(main, "apply_migrations", must_not_run, raising=False)

    app = main.create_app()

    assert app.title == "共演計劃 API"


class _ReadinessConnection:
    def __init__(
        self,
        versions=(
            "001_create_rooms",
            "002_create_story_jobs",
            "003_create_story_resolution_results",
            "004_create_support_report_drafts",
            "005_create_story_job_dispatch_outbox",
        ),
        failure=None,
    ):
        self.versions = versions
        self.failure = failure
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        if self.failure:
            raise self.failure
        normalized = " ".join(sql.lower().split())
        if "select 1" in normalized:
            return _Result([(1,)])
        if "schema_migrations" in normalized:
            return _Result([(version,) for version in self.versions])
        raise AssertionError(f"readiness 不應探測非必要資料表：{sql}")


def _postgres_repository(monkeypatch, connection):
    module = importlib.import_module("app.adapters.postgres_room_repository")
    monkeypatch.setattr(
        module,
        "psycopg",
        SimpleNamespace(connect=lambda dsn: connection),
    )
    return module.PostgresRoomRepository("postgresql://test/ignored")


def test_postgres_readiness_requires_database_and_current_schema(monkeypatch) -> None:
    connection = _ReadinessConnection()
    repository = _postgres_repository(monkeypatch, connection)
    probe = getattr(repository, "is_ready", None)

    assert callable(probe), "PostgresRoomRepository 尚未提供 migration-aware is_ready()"
    assert probe() is True
    statements = [sql.lower() for sql, _ in connection.statements]
    assert any("select 1" in sql for sql in statements)
    assert any("schema_migrations" in sql for sql in statements)
    assert not any(" from rooms" in sql for sql in statements)


@pytest.mark.parametrize(
    "connection",
    [
        _ReadinessConnection(versions=()),
        _ReadinessConnection(versions=("001_create_rooms", "999_unknown")),
        _ReadinessConnection(failure=RuntimeError("database unavailable")),
    ],
)
def test_postgres_readiness_returns_false_for_stale_or_unavailable_database(
    monkeypatch, connection
) -> None:
    repository = _postgres_repository(monkeypatch, connection)
    probe = getattr(repository, "is_ready", None)

    assert callable(probe), "PostgresRoomRepository 尚未提供 migration-aware is_ready()"
    assert probe() is False
