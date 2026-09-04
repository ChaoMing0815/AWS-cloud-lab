import sys
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.postgres_room_repository import PostgresRoomRepository
from app.main import create_app
import app.main as main_module


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
        "CO_STORY_RESOLUTION_MODE",
        "CO_STORY_AWS_REGION",
        "CO_STORY_BEDROCK_MODEL_ID",
        "CO_STORY_BEDROCK_GUARDRAIL_ID",
        "CO_STORY_BEDROCK_GUARDRAIL_VERSION",
        "CO_STORY_BEDROCK_MAX_TOKENS",
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
    monkeypatch.setenv("CO_STORY_RESOLUTION_MODE", "async")


def configure_bedrock(monkeypatch, *, max_tokens: str = "800") -> None:
    monkeypatch.setenv("CO_STORY_AWS_REGION", "ap-northeast-1")
    monkeypatch.setenv("CO_STORY_BEDROCK_MODEL_ID", "anthropic.claude-test-v1")
    monkeypatch.setenv("CO_STORY_BEDROCK_GUARDRAIL_ID", "gr-story-safety")
    monkeypatch.setenv("CO_STORY_BEDROCK_GUARDRAIL_VERSION", "7")
    monkeypatch.setenv("CO_STORY_BEDROCK_MAX_TOKENS", max_tokens)


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


@pytest.mark.parametrize(
    "name",
    [
        "CO_STORY_AWS_REGION",
        "CO_STORY_BEDROCK_MODEL_ID",
        "CO_STORY_BEDROCK_GUARDRAIL_ID",
        "CO_STORY_BEDROCK_GUARDRAIL_VERSION",
        "CO_STORY_BEDROCK_MAX_TOKENS",
    ],
)
def test_production_default_storyteller_requires_each_bedrock_setting(monkeypatch, name) -> None:
    configure_production(monkeypatch)
    configure_bedrock(monkeypatch)
    monkeypatch.delenv(name)

    with pytest.raises(RuntimeError) as error:
        create_app()

    assert str(error.value) == name


@pytest.mark.parametrize("max_tokens", ["0", "3001", "not-an-integer"])
def test_production_default_storyteller_rejects_invalid_bedrock_token_limit(monkeypatch, max_tokens) -> None:
    configure_production(monkeypatch)
    configure_bedrock(monkeypatch, max_tokens=max_tokens)

    with pytest.raises(RuntimeError) as error:
        create_app()

    assert str(error.value) == "CO_STORY_BEDROCK_MAX_TOKENS"


def test_production_default_storyteller_builds_bedrock_without_calling_runtime(monkeypatch) -> None:
    configure_production(monkeypatch)
    configure_bedrock(monkeypatch)
    client_calls = []

    class FakeConfig:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    runtime_client = object()

    def fake_client(service_name, *, region_name, config):
        client_calls.append((service_name, region_name, config))
        return runtime_client

    fake_boto3 = ModuleType("boto3")
    fake_boto3.client = fake_client
    fake_botocore = ModuleType("botocore")
    fake_config_module = ModuleType("botocore.config")
    fake_config_module.Config = FakeConfig
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setitem(sys.modules, "botocore", fake_botocore)
    monkeypatch.setitem(sys.modules, "botocore.config", fake_config_module)

    app = create_app()

    assert isinstance(app.state.room_service.repository, PostgresRoomRepository)
    assert type(app.state.room_service.storyteller).__name__ == "BedrockStoryteller"
    assert len(client_calls) == 1
    service_name, region_name, config = client_calls[0]
    assert service_name == "bedrock-runtime"
    assert region_name == "ap-northeast-1"
    assert config.kwargs["read_timeout"] == 30
    assert config.kwargs["connect_timeout"] <= 5
    assert config.kwargs["retries"] == {"max_attempts": 0}


def test_explicit_production_storyteller_does_not_require_bedrock_settings(monkeypatch) -> None:
    configure_production(monkeypatch)

    app = create_app(
        room_repository=MemoryRoomRepository(),
        storyteller=FakeProductionStoryteller(),
    )

    assert app.state.room_service.storyteller.__class__ is FakeProductionStoryteller


def test_production_with_injected_dependencies_does_not_seed_bonus7_demo_room(monkeypatch) -> None:
    configure_production(monkeypatch)
    repository = MemoryRoomRepository()

    create_app(room_repository=repository, storyteller=FakeProductionStoryteller())

    assert repository.get_by_code("BONUS7") is None


def test_postgres_composition_enables_async_producer_without_worker_in_web_process(
    monkeypatch,
) -> None:
    configure_production(monkeypatch)
    repository = MemoryRoomRepository()
    created = {}

    class RecordingStore:
        def __init__(self, dsn, *, clock):
            created["store"] = (dsn, clock)

    class RecordingProducer:
        def __init__(self, store):
            self._store = store
            created["producer_store"] = store

    monkeypatch.setattr(main_module, "PostgresRoomRepository", lambda dsn: repository)
    monkeypatch.setattr(
        main_module,
        "PostgresStoryResolutionStore",
        RecordingStore,
        raising=False,
    )
    monkeypatch.setattr(
        main_module,
        "StoryResolutionProducer",
        RecordingProducer,
        raising=False,
    )

    app = create_app(storyteller=FakeProductionStoryteller())

    assert app.state.room_service.async_story_resolution_enabled is True
    assert created["producer_store"] is app.state.room_service.story_resolution_producer._store
    assert not hasattr(app.state, "story_resolution_worker")


def test_sync_resolution_mode_keeps_postgres_web_flow_on_existing_200_path(monkeypatch) -> None:
    configure_production(monkeypatch)
    monkeypatch.setenv("CO_STORY_RESOLUTION_MODE", "sync")
    repository = MemoryRoomRepository()
    monkeypatch.setattr(main_module, "PostgresRoomRepository", lambda _dsn: repository)
    monkeypatch.setattr(
        main_module,
        "StoryResolutionProducer",
        lambda _store: pytest.fail("sync bridge must not construct a StoryJob producer"),
        raising=False,
    )

    app = create_app(storyteller=FakeProductionStoryteller())

    assert app.state.room_service.async_story_resolution_enabled is False


@pytest.mark.parametrize("mode", (None, "", "ASYNC", " async", "async ", "unknown"))
def test_production_web_requires_an_exact_resolution_mode_before_producer_or_store(
    monkeypatch, mode
) -> None:
    configure_production(monkeypatch)
    if mode is None:
        monkeypatch.delenv("CO_STORY_RESOLUTION_MODE", raising=False)
    else:
        monkeypatch.setenv("CO_STORY_RESOLUTION_MODE", mode)
    monkeypatch.setattr(
        main_module,
        "PostgresStoryResolutionStore",
        lambda *_args, **_kwargs: pytest.fail("invalid production mode must stop before store creation"),
    )

    with pytest.raises(RuntimeError, match="CO_STORY_RESOLUTION_MODE"):
        create_app(storyteller=FakeProductionStoryteller())


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
