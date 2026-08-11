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
        self.applied_versions = set(applied_versions)
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
            return _Result([(version,) for version in sorted(self.applied_versions)])
        if "insert into schema_migrations" in normalized:
            self.applied_versions.add(params[0])
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
    _write_migration(tmp_path, "010_add_story_index.sql", "ten")
    connection = _MigrationConnection(applied_versions={"001_create_rooms"})
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
    assert connection.applied_versions == {"001_create_rooms", "010_add_story_index"}
    assert sum("-- ten" in sql for sql in executed_sql) == 1
    assert not any("-- one" in sql for sql in executed_sql)
    version_inserts = [
        params
        for sql, params in connection.statements
        if "insert into schema_migrations" in sql.lower()
    ]
    assert version_inserts == [("010_add_story_index",)]
    assert connection.transaction_count == 1


@pytest.mark.parametrize("filenames", [("001_create_rooms.sql", "001_duplicate.sql"), ("001_create_rooms.sql", "not-a-migration.sql")])
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
    def __init__(self, versions=("001_create_rooms",), failure=None):
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
