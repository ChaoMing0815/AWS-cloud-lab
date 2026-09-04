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
        "CO_STORY_RESOLUTION_MODE",
        "CO_STORY_SQS_QUEUE_URL",
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
    monkeypatch.setenv("CO_STORY_RESOLUTION_MODE", "async")
    monkeypatch.setenv(
        "CO_STORY_SQS_QUEUE_URL",
        "https://sqs.ap-northeast-1.amazonaws.com/123456789012/co-story-tier2-story",
    )


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
        ("CO_STORY_SQS_QUEUE_URL", None),
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

    class FakeSqsClient:
        def __init__(self) -> None:
            self.receive_calls = 0

        def receive_message(self, **_kwargs):
            self.receive_calls += 1
            raise AssertionError("SQS receive should not run during construction")

    sqs_client = FakeSqsClient()

    def fake_client(_region: str, config=None):
        return client

    monkeypatch.setattr(factory_module, "_create_bedrock_client", fake_client)
    assert hasattr(factory_module, "_create_sqs_client"), "production SQS client factory 尚未建立"
    monkeypatch.setattr(
        factory_module,
        "_create_sqs_client",
        lambda _region, config=None: sqs_client,
    )

    runner = factory_module.build_production_worker("postgresql://app:secret@localhost/co_story")

    assert client.calls == 0
    assert sqs_client.receive_calls == 0
    assert runner.__class__.__name__ == "SqsStoryResolutionWorkerRunner"


def test_production_storyteller_accepts_bounded_tooluse_hotfix_budget(monkeypatch) -> None:
    _configure_production_env(monkeypatch)
    monkeypatch.setenv("CO_STORY_BEDROCK_MAX_TOKENS", "3000")
    factory_module, _ = _load_modules(monkeypatch)
    created = {}

    class RecordingStoryteller:
        def __init__(self, **settings):
            created.update(settings)

    monkeypatch.setattr(factory_module, "BedrockStoryteller", RecordingStoryteller)
    monkeypatch.setattr(
        factory_module,
        "_create_bedrock_client",
        lambda _region, config=None: object(),
    )

    factory_module.create_production_bedrock_storyteller()

    assert created["max_tokens"] == 3000


@pytest.mark.parametrize(
    "queue_url",
    [
        "http://sqs.ap-northeast-1.amazonaws.com/123456789012/co-story-tier2-story",
        "https://sqs.us-east-1.amazonaws.com/123456789012/co-story-tier2-story",
        "https://sqs.ap-northeast-1.amazonaws.com/123456789012/other-queue",
        " https://sqs.ap-northeast-1.amazonaws.com/123456789012/co-story-tier2-story",
    ],
)
def test_production_worker_rejects_noncanonical_queue_url_before_clients(
    monkeypatch, queue_url
) -> None:
    _configure_production_env(monkeypatch)
    monkeypatch.setenv("CO_STORY_SQS_QUEUE_URL", queue_url)
    factory_module, _ = _load_modules(monkeypatch)
    monkeypatch.setattr(
        factory_module,
        "_create_bedrock_client",
        lambda *_args, **_kwargs: pytest.fail("invalid queue URL must stop before Bedrock"),
    )

    with pytest.raises(RuntimeError) as captured:
        factory_module.build_production_worker("postgresql://app:secret@localhost/co_story")

    assert str(captured.value) == "CO_STORY_SQS_QUEUE_URL"


def test_production_sqs_runner_aligns_db_lease_and_attempts_with_transport(
    monkeypatch,
) -> None:
    _configure_production_env(monkeypatch)
    factory_module, _ = _load_modules(monkeypatch)
    created = {}

    class RecordingQueue:
        def __init__(self, dsn, *, clock, lease_duration, max_attempts):
            created["queue"] = (dsn, clock, lease_duration, max_attempts)

    class RecordingStore:
        def __init__(self, dsn, *, clock):
            created["store"] = (dsn, clock)

    class FakeSqsClient:
        pass

    monkeypatch.setattr(
        "app.adapters.postgres_story_job_queue.PostgresStoryJobQueue",
        RecordingQueue,
    )
    monkeypatch.setattr(
        "app.adapters.postgres_story_resolution_store.PostgresStoryResolutionStore",
        RecordingStore,
    )
    monkeypatch.setattr(factory_module, "create_production_story_resolution_narrator", object)
    assert hasattr(factory_module, "_create_sqs_client"), "production SQS client factory 尚未建立"
    monkeypatch.setattr(
        factory_module,
        "_create_sqs_client",
        lambda _region, config=None: FakeSqsClient(),
    )

    runner = factory_module.build_production_worker_runner(
        database_url="postgresql://app:secret@localhost/co_story",
        worker_id="worker-1",
    )

    assert runner.__class__.__name__ == "SqsStoryResolutionWorkerRunner"
    assert created["queue"][2].total_seconds() == 180
    assert created["queue"][3] == 3


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


@pytest.mark.parametrize("mode", (None, "", "sync", "ASYNC", " async", "async ", "unknown"))
def test_production_worker_requires_literal_async_before_runner_queue_or_bedrock(
    monkeypatch, mode
) -> None:
    _configure_production_env(monkeypatch)
    if mode is None:
        monkeypatch.delenv("CO_STORY_RESOLUTION_MODE", raising=False)
    else:
        monkeypatch.setenv("CO_STORY_RESOLUTION_MODE", mode)
    factory_module, _ = _load_modules(monkeypatch)
    monkeypatch.setattr(
        factory_module,
        "build_production_worker_runner",
        lambda **_kwargs: pytest.fail("invalid mode must stop before queue or Bedrock construction"),
    )

    with pytest.raises(RuntimeError, match="CO_STORY_RESOLUTION_MODE"):
        factory_module.build_production_worker("postgresql://app:secret@localhost/co_story")


def test_worker_main_uses_production_path_in_production_environment(monkeypatch, capsys) -> None:
    _configure_production_env(monkeypatch)
    _, worker_module = _load_modules(monkeypatch)

    class FakeRunner:
        def run_once(self) -> str:
            raise AssertionError("production worker must use the long-poll loop")

        def run_forever(self) -> str:
            return "stopped"

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
    assert output == "worker_result=stopped"


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
