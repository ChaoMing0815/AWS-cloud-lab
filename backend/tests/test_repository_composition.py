import inspect

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.postgres_room_repository import PostgresRoomRepository
from app.main import create_app


def test_create_app_accepts_and_uses_room_repository_dependency() -> None:
    signature = inspect.signature(create_app)

    assert "room_repository" in signature.parameters

    repository = MemoryRoomRepository()
    app = create_app(room_repository=repository)

    assert app.state.room_service.repository is repository


def test_create_app_uses_postgres_only_when_database_url_is_set(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://db.invalid/co_story")

    app = create_app()

    repository = app.state.room_service.repository
    assert isinstance(repository, PostgresRoomRepository)
    assert repository.dsn == "postgresql://db.invalid/co_story"


def test_explicit_repository_overrides_database_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://db.invalid/co_story")
    repository = MemoryRoomRepository()

    app = create_app(room_repository=repository)

    assert app.state.room_service.repository is repository
