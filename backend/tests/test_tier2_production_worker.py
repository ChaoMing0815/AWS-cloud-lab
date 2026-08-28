from __future__ import annotations

import importlib
import sys
from types import ModuleType

import pytest


def _install_psycopg_stub(monkeypatch) -> None:
    if "psycopg" in sys.modules:
        return

    psycopg = ModuleType("psycopg")
    types = ModuleType("psycopg.types")
    json_module = ModuleType("psycopg.types.json")

    class FakeJsonb:
        def __init__(self, payload):
            self.payload = payload

        def __iter__(self):
            return iter(self.payload)

    json_module.Jsonb = FakeJsonb
    types.json = json_module
    psycopg.types = types
    monkeypatch.setitem(sys.modules, "psycopg", psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.types", types)
    monkeypatch.setitem(sys.modules, "psycopg.types.json", json_module)

    if "botocore" not in sys.modules:
        botocore = ModuleType("botocore")
        config = ModuleType("botocore.config")

        class FakeConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        config.Config = FakeConfig
        botocore.config = config
        monkeypatch.setitem(sys.modules, "botocore", botocore)
        monkeypatch.setitem(sys.modules, "botocore.config", config)


def _load_modules(monkeypatch):
    _install_psycopg_stub(monkeypatch)
    assert (
        importlib.util.find_spec("app.adapters.production_storyteller_factory") is not None
    ), "production storyteller factory module should be introduced in this slice"
    factory_module = importlib.reload(
        importlib.import_module("app.adapters.production_storyteller_factory")
    )
    worker_module = importlib.reload(
        importlib.import_module("app.workers.story_resolution_worker")
    )
    return factory_module, worker_module


def _configure_production_env(monkeypatch, *, dsn: str = "postgresql://app:secret@localhost/co_story"):
    for name in (
        "CO_STORY_ENV",
        "CO_STORY_AWS_REGION",
        "CO_STORY_BEDROCK_MODEL_ID",
        "CO_STORY_BEDROCK_GUARDRAIL_ID",
        "CO_STORY_BEDROCK_GUARDRAIL_VERSION",
        "CO_STORY_BEDROCK_MAX_TOKENS",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CO_STORY_ENV", "production")
    if dsn is not None:
        monkeypatch.setenv("DATABASE_URL", dsn)
    else:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("CO_STORY_AWS_REGION", "ap-northeast-1")
    monkeypatch.setenv("CO_STORY_BEDROCK_MODEL_ID", "anthropic.claude-test-v1")
    monkeypatch.setenv("CO_STORY_BEDROCK_GUARDRAIL_ID", "gr-story-safety")
    monkeypatch.setenv("CO_STORY_BEDROCK_GUARDRAIL_VERSION", "7")
    monkeypatch.setenv("CO_STORY_BEDROCK_MAX_TOKENS", "800")


@pytest.mark.parametrize(
    (
        "name",
        "value",
    ),
    [
        ("CO_STORY_AWS_REGION", None),
        ("CO_STORY_BEDROCK_MODEL_ID", None),
        ("CO_STORY_BEDROCK_GUARDRAIL_ID", None),
        ("CO_STORY_BEDROCK_GUARDRAIL_VERSION", None),
        ("CO_STORY_BEDROCK_MAX_TOKENS", "0"),
    ],
)
def test_production_worker_build_rejects_missing_or_invalid_bootstrap_config(
    monkeypatch,
    name,
    value,
) -> None:
    _configure_production_env(monkeypatch)
    if value is None:
        monkeypatch.delenv(name, raising=False)
    else:
        monkeypatch.setenv(name, value)

    factory_module, _ = _load_modules(monkeypatch)
    called = {"client": 0}

    def fake_client(region: str, config=None):
        called["client"] += 1
        raise AssertionError("bedrock client should never be created")

    monkeypatch.setattr(factory_module, "_create_bedrock_client", fake_client)

    with pytest.raises(RuntimeError) as captured:
        factory_module.build_production_worker("postgresql://app:secret@localhost/co_story")

    assert str(captured.value) == name
    assert called["client"] == 0


def test_build_production_worker_constructs_without_converse(monkeypatch) -> None:
    _configure_production_env(monkeypatch)
    factory_module, _ = _load_modules(monkeypatch)

    class FakeClient:
        def __init__(self) -> None:
            self.calls = 0

        def converse(self, **_kwargs) -> None:
            self.calls += 1
            raise AssertionError("converse should not be called during construction")

    client = FakeClient()

    def fake_client(_region: str, config=None):
        return client

    monkeypatch.setattr(factory_module, "_create_bedrock_client", fake_client)

    runner = factory_module.build_production_worker("postgresql://app:secret@localhost/co_story")

    assert client.calls == 0
    assert runner.__class__.__name__ == "LocalStoryResolutionWorkerRunner"


def test_production_worker_factory_rejects_sync_mode_before_queue_or_bedrock(monkeypatch) -> None:
    _configure_production_env(monkeypatch)
    monkeypatch.setenv("CO_STORY_RESOLUTION_MODE", "sync")
    factory_module, _ = _load_modules(monkeypatch)
    monkeypatch.setattr(
        factory_module,
        "build_production_worker_runner",
        lambda **_kwargs: pytest.fail("sync mode must stop before queue or Bedrock construction"),
    )

    with pytest.raises(RuntimeError, match="CO_STORY_RESOLUTION_MODE"):
        factory_module.build_production_worker("postgresql://app:secret@localhost/co_story")


def test_worker_main_uses_production_path_in_production_environment(monkeypatch, capsys) -> None:
    _configure_production_env(monkeypatch)
    _, worker_module = _load_modules(monkeypatch)

    class FakeRunner:
        def run_once(self) -> str:
            return "processed"

    monkeypatch.setattr(
        worker_module,
        "build_production_runner",
        lambda dsn, worker_id=None: FakeRunner(),
    )
    monkeypatch.setattr(
        worker_module,
        "build_local_runner",
        lambda dsn, worker_id=None: pytest.fail("local runner must not run in production"),
    )

    assert worker_module.main() == 0
    output = capsys.readouterr().out.strip()
    assert output == "worker_result=processed"


def test_worker_main_local_mode_still_uses_mock_runner(monkeypatch, capsys) -> None:
    _configure_production_env(monkeypatch)
    _, worker_module = _load_modules(monkeypatch)
    monkeypatch.delenv("CO_STORY_ENV", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    class FakeLocalRunner:
        def run_once(self) -> str:
            return "idle"

    monkeypatch.setattr(
        worker_module,
        "build_local_runner",
        lambda dsn, worker_id=None: FakeLocalRunner(),
    )

    monkeypatch.setenv("DATABASE_URL", "postgresql://app:secret@localhost/co_story")
    assert worker_module.main() == 0
    assert capsys.readouterr().out.strip() == "worker_result=idle"


def test_worker_main_stops_without_database_url(monkeypatch, capsys) -> None:
    _configure_production_env(monkeypatch, dsn="")
    _, worker_module = _load_modules(monkeypatch)
    assert worker_module.main() == 2
    assert capsys.readouterr().out.strip() == "worker_result=stopped:database_url_missing"
