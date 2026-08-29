from __future__ import annotations

import importlib
import importlib.util
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import pytest


def _module():
    spec = importlib.util.find_spec("app.workers.story_resolution_worker_bootstrap")
    assert spec is not None, "production Worker secret bootstrap 尚未建立"
    return importlib.import_module("app.workers.story_resolution_worker_bootstrap")


class FakeSecretsClient:
    def __init__(self, payload=None, *, error: Exception | None = None) -> None:
        self.payload = payload
        self.error = error
        self.calls = []

    def get_secret_value(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return {"SecretString": json.dumps(self.payload)}


def test_bootstrap_reads_only_exact_secret_and_builds_verify_full_database_url(tmp_path) -> None:
    module = _module()
    ca = tmp_path / "rds-ca.pem"
    ca.write_text("test-ca", encoding="utf-8")
    secret_arn = (
        "arn:aws:secretsmanager:ap-northeast-1:123456789012:"
        "secret:co-story-runtime-AbCdEf"
    )
    client = FakeSecretsClient(
        {"username": "co_story_app", "password": "space and:/@?#%+secret"}
    )

    database_url = module.load_database_url(
        client,
        region="ap-northeast-1",
        secret_arn=secret_arn,
        endpoint="co-story.cluster.ap-northeast-1.rds.amazonaws.com",
        ca_path=ca,
    )

    parsed = urlsplit(database_url)
    assert unquote(parsed.username) == "co_story_app"
    assert unquote(parsed.password) == "space and:/@?#%+secret"
    assert parsed.hostname == "co-story.cluster.ap-northeast-1.rds.amazonaws.com"
    assert parsed.port == 5432
    assert parsed.path == "/co_story"
    assert parse_qs(parsed.query) == {
        "sslmode": ["verify-full"],
        "sslrootcert": [str(ca)],
    }
    assert client.calls == [{"SecretId": secret_arn}]


@pytest.mark.parametrize(
    ("region", "secret_arn", "endpoint"),
    [
        (
            "ap-northeast-1",
            "arn:aws:secretsmanager:us-east-1:123456789012:secret:co-story-runtime-AbCdEf",
            "co-story.cluster.ap-northeast-1.rds.amazonaws.com",
        ),
        (
            "ap-northeast-1",
            "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:co-story-runtime-AbCdEf",
            "db.example.test",
        ),
        (
            " ap-northeast-1",
            "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:co-story-runtime-AbCdEf",
            "co-story.cluster.ap-northeast-1.rds.amazonaws.com",
        ),
    ],
)
def test_bootstrap_rejects_cross_region_or_non_rds_configuration_before_secret_read(
    tmp_path, region, secret_arn, endpoint
) -> None:
    module = _module()
    ca = tmp_path / "rds-ca.pem"
    ca.write_text("test-ca", encoding="utf-8")
    client = FakeSecretsClient({"username": "co_story_app", "password": "secret"})

    with pytest.raises(module.WorkerBootstrapError):
        module.load_database_url(
            client,
            region=region,
            secret_arn=secret_arn,
            endpoint=endpoint,
            ca_path=ca,
        )

    assert client.calls == []


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "postgres", "password": "secret"},
        {"username": "co_story_app", "password": ""},
        {"username": "co_story_app"},
        {"username": "co_story_app", "password": "secret", "extra": "forbidden"},
    ],
)
def test_bootstrap_rejects_unexpected_secret_shape_without_echoing_values(
    tmp_path, payload
) -> None:
    module = _module()
    ca = tmp_path / "rds-ca.pem"
    ca.write_text("test-ca", encoding="utf-8")
    client = FakeSecretsClient(payload)

    with pytest.raises(module.WorkerBootstrapError) as captured:
        module.load_database_url(
            client,
            region="ap-northeast-1",
            secret_arn=(
                "arn:aws:secretsmanager:ap-northeast-1:123456789012:"
                "secret:co-story-runtime-AbCdEf"
            ),
            endpoint="co-story.cluster.ap-northeast-1.rds.amazonaws.com",
            ca_path=ca,
        )

    assert str(captured.value) == "runtime_secret_invalid"
    assert "secret" not in str(captured.value).replace("runtime_secret_invalid", "")


def test_bootstrap_rejects_missing_or_symlinked_ca_before_secret_read(tmp_path) -> None:
    module = _module()
    real_ca = tmp_path / "real.pem"
    real_ca.write_text("test-ca", encoding="utf-8")
    symlink = tmp_path / "rds-ca.pem"
    symlink.symlink_to(real_ca)
    client = FakeSecretsClient({"username": "co_story_app", "password": "secret"})

    with pytest.raises(module.WorkerBootstrapError, match="rds_ca_invalid"):
        module.load_database_url(
            client,
            region="ap-northeast-1",
            secret_arn=(
                "arn:aws:secretsmanager:ap-northeast-1:123456789012:"
                "secret:co-story-runtime-AbCdEf"
            ),
            endpoint="co-story.cluster.ap-northeast-1.rds.amazonaws.com",
            ca_path=symlink,
        )

    assert client.calls == []


def test_bootstrap_main_sets_database_url_in_memory_and_never_prints_it(
    monkeypatch, tmp_path, capsys
) -> None:
    module = _module()
    ca = tmp_path / "rds-ca.pem"
    ca.write_text("test-ca", encoding="utf-8")
    monkeypatch.setenv("CO_STORY_AWS_REGION", "ap-northeast-1")
    monkeypatch.setenv(
        "CO_STORY_RUNTIME_SECRET_ARN",
        "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:co-story-runtime-AbCdEf",
    )
    monkeypatch.setenv(
        "CO_STORY_DB_ENDPOINT",
        "co-story.cluster.ap-northeast-1.rds.amazonaws.com",
    )
    monkeypatch.setenv("CO_STORY_RDS_CA_PATH", str(ca))
    client = FakeSecretsClient({"username": "co_story_app", "password": "never-print"})
    observed = {}

    def worker_main():
        observed["database_url"] = os.environ["DATABASE_URL"]
        return 0

    assert module.main(create_client=lambda _region: client, run_worker=worker_main) == 0
    captured = capsys.readouterr()
    assert "never-print" not in captured.out
    assert "never-print" not in captured.err
    assert "never-print" in observed["database_url"]


def test_bootstrap_main_sanitizes_secret_client_failure(monkeypatch, tmp_path, capsys) -> None:
    module = _module()
    ca = tmp_path / "rds-ca.pem"
    ca.write_text("test-ca", encoding="utf-8")
    monkeypatch.setenv("CO_STORY_AWS_REGION", "ap-northeast-1")
    monkeypatch.setenv(
        "CO_STORY_RUNTIME_SECRET_ARN",
        "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:co-story-runtime-AbCdEf",
    )
    monkeypatch.setenv(
        "CO_STORY_DB_ENDPOINT",
        "co-story.cluster.ap-northeast-1.rds.amazonaws.com",
    )
    monkeypatch.setenv("CO_STORY_RDS_CA_PATH", str(ca))
    client = FakeSecretsClient(error=RuntimeError("provider-secret-detail"))

    assert module.main(create_client=lambda _region: client, run_worker=lambda: 0) == 2
    captured = capsys.readouterr()
    assert captured.out.strip() == "worker_bootstrap=stopped:runtime_secret_unavailable"
    assert "provider-secret-detail" not in captured.out
    assert "provider-secret-detail" not in captured.err
