import inspect
import os

import psycopg
import pytest

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.postgres_room_repository import PostgresRoomRepository
from app.adapters.postgres_migrations import apply_migrations
from app.main import create_app


def test_create_app_accepts_and_uses_room_repository_dependency() -> None:
    signature = inspect.signature(create_app)

    assert "room_repository" in signature.parameters

    repository = MemoryRoomRepository()
    app = create_app(room_repository=repository)

    assert app.state.room_service.repository is repository


def test_create_app_uses_postgres_only_when_database_url_is_set(monkeypatch) -> None:
    dsn = os.environ.get("CO_STORY_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("CO_STORY_TEST_DATABASE_URL is required for PostgreSQL composition test")
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM rooms")
    monkeypatch.setenv("DATABASE_URL", dsn)

    app = create_app()

    repository = app.state.room_service.repository
    assert isinstance(repository, PostgresRoomRepository)
    assert repository.dsn == dsn


def test_explicit_repository_overrides_database_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://db.invalid/co_story")
    repository = MemoryRoomRepository()

    app = create_app(room_repository=repository)

    assert app.state.room_service.repository is repository
