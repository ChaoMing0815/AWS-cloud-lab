from __future__ import annotations

import importlib
import importlib.util
from types import SimpleNamespace

import pytest


def _runtime_module():
    spec = importlib.util.find_spec("app.workers.story_job_publisher")
    assert spec is not None, "StoryJob publisher runtime 尚未建立"
    return importlib.import_module("app.workers.story_job_publisher")


def _factory_module():
    return importlib.import_module("app.adapters.production_storyteller_factory")


def _configure(monkeypatch) -> None:
    monkeypatch.setenv("CO_STORY_ENV", "production")
    monkeypatch.setenv("CO_STORY_RESOLUTION_MODE", "async")
    monkeypatch.setenv("CO_STORY_PUBLISHER_ENABLED", "true")
    monkeypatch.setenv("CO_STORY_AWS_REGION", "ap-northeast-1")
    monkeypatch.setenv(
        "CO_STORY_SQS_QUEUE_URL",
        "https://sqs.ap-northeast-1.amazonaws.com/123456789012/co-story-tier2-story",
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://app:redacted@db/co_story")


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("CO_STORY_ENV", "staging"),
        ("CO_STORY_RESOLUTION_MODE", "sync"),
        ("CO_STORY_PUBLISHER_ENABLED", "false"),
        ("CO_STORY_PUBLISHER_ENABLED", "TRUE"),
        ("DATABASE_URL", ""),
    ],
)
def test_production_publisher_requires_explicit_enable_before_aws_or_database(
    monkeypatch, name, value
) -> None:
    _configure(monkeypatch)
    monkeypatch.setenv(name, value)
    factory = _factory_module()
    monkeypatch.setattr(
        factory,
        "_create_sqs_client",
        lambda *_args, **_kwargs: pytest.fail("disabled publisher must not create AWS client"),
    )

    with pytest.raises(RuntimeError, match=name):
        factory.build_production_story_job_publisher(
            "postgresql://app:redacted@db/co_story"
            if name != "DATABASE_URL"
            else value
        )


def test_production_publisher_builds_without_database_or_sqs_io(monkeypatch) -> None:
    _configure(monkeypatch)
    factory = _factory_module()
    calls = []

    class SqsClient:
        def send_message(self, **_kwargs):
            calls.append("send")

    monkeypatch.setattr(factory, "_create_sqs_client", lambda *_args, **_kwargs: SqsClient())

    publisher = factory.build_production_story_job_publisher(
        "postgresql://app:redacted@db/co_story"
    )

    assert publisher.__class__.__name__ == "StoryJobPublisher"
    assert calls == []


class StopAfterTwoWaits:
    def __init__(self) -> None:
        self.waits = []

    def is_set(self) -> bool:
        return False

    def wait(self, seconds: float) -> bool:
        self.waits.append(seconds)
        return len(self.waits) == 2


def test_runtime_reconciles_continuously_without_busy_loop(monkeypatch) -> None:
    module = _runtime_module()
    outcomes = iter(["published", "idle"])
    publisher = SimpleNamespace(run_once=lambda: next(outcomes))
    stop = StopAfterTwoWaits()

    assert module.run_publisher(publisher, stop_event=stop) == "stopped"
    assert stop.waits == [0, 1]


def test_runtime_main_sanitizes_bootstrap_failure(monkeypatch, capsys) -> None:
    _configure(monkeypatch)
    module = _runtime_module()
    monkeypatch.setattr(
        module,
        "build_production_story_job_publisher",
        lambda _dsn: (_ for _ in ()).throw(RuntimeError("provider secret detail")),
    )

    assert module.main() == 2
    captured = capsys.readouterr()
    assert captured.out.strip() == "publisher_result=stopped:publisher_bootstrap_failure"
    assert "provider secret detail" not in captured.out
    assert "provider secret detail" not in captured.err


def test_runtime_main_never_starts_without_database_url(monkeypatch, capsys) -> None:
    _configure(monkeypatch)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    module = _runtime_module()

    assert module.main() == 2
    assert capsys.readouterr().out.strip() == "publisher_result=stopped:database_url_missing"
