import pytest
from fastapi.testclient import TestClient

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.main import create_app


class FakeProductionStoryteller:
    def resolve_round(self, _room) -> str:
        return "正式測試敘事"

    def resolve_ending(self, _room) -> str:
        return "正式測試結局"


def configure_production(monkeypatch, *, database_url: str | None = None) -> None:
    for name in (
        "CO_STORY_ENV",
        "DATABASE_URL",
        "CO_STORY_COOKIE_SECURE",
        "CO_STORY_ALLOWED_HOSTS",
        "CO_STORY_ALLOWED_ORIGINS",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CO_STORY_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        database_url
        or "postgresql://app:secret@db.example.test/co_story?sslmode=verify-full&sslrootcert=/run/certs/rds-ca.pem",
    )
    monkeypatch.setenv("CO_STORY_COOKIE_SECURE", "true")
    monkeypatch.setenv("CO_STORY_ALLOWED_HOSTS", "app.example.test")
    monkeypatch.setenv("CO_STORY_ALLOWED_ORIGINS", "https://app.example.test")


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("DATABASE_URL", None),
        ("CO_STORY_COOKIE_SECURE", "false"),
        ("CO_STORY_ALLOWED_HOSTS", None),
        ("CO_STORY_ALLOWED_ORIGINS", None),
    ],
)
def test_production_rejects_missing_required_composition_setting(monkeypatch, name, value) -> None:
    configure_production(monkeypatch)
    if value is None:
        monkeypatch.delenv(name, raising=False)
    else:
        monkeypatch.setenv(name, value)

    with pytest.raises(RuntimeError, match=name):
        create_app(
            room_repository=MemoryRoomRepository(),
            storyteller=FakeProductionStoryteller(),
        )


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql://app:secret@db.example.test/co_story?sslmode=require&sslrootcert=/run/certs/rds-ca.pem",
        "postgresql://app:secret@db.example.test/co_story?sslmode=verify-full",
    ],
)
def test_production_rejects_database_url_without_full_tls_verification(monkeypatch, database_url) -> None:
    configure_production(monkeypatch, database_url=database_url)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        create_app(
            room_repository=MemoryRoomRepository(),
            storyteller=FakeProductionStoryteller(),
        )


def test_production_rejects_default_mock_storyteller(monkeypatch) -> None:
    configure_production(monkeypatch)

    with pytest.raises(RuntimeError, match="storyteller"):
        create_app(room_repository=MemoryRoomRepository())


def test_production_with_injected_dependencies_does_not_seed_bonus7_demo_room(monkeypatch) -> None:
    configure_production(monkeypatch)
    repository = MemoryRoomRepository()

    create_app(room_repository=repository, storyteller=FakeProductionStoryteller())

    assert repository.get_by_code("BONUS7") is None


def test_session_and_local_room_cookies_last_one_week() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/rooms",
            json={"nickname": "房主"},
            headers={"Idempotency-Key": "one-week-cookie-lifetime"},
        )

    assert response.status_code == 201
    cookies = response.headers.get_list("set-cookie")
    for name in ("co_story_local_room", "co_story_host", "co_story_player"):
        cookie = next(value for value in cookies if value.startswith(f"{name}="))
        assert "Max-Age=604800" in cookie
