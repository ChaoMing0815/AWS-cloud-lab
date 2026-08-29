from pathlib import Path
import shlex

import pytest


ROOT = Path(__file__).parents[2]
DOCKERFILE = ROOT / "Dockerfile"
WORKER_UNIT = ROOT / "ops/systemd/co-story-worker-container.service"


def _read(path: Path) -> str:
    assert path.is_file(), f"Tier 2 Worker asset 尚未建立：{path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def _execstart_tokens(unit: str) -> list[str]:
    command = next(
        line.removeprefix("ExecStart=")
        for line in unit.splitlines()
        if line.startswith("ExecStart=")
    )
    return shlex.split(command)


def _assert_worker_unit_contract(unit: str) -> None:
    tokens = _execstart_tokens(unit)

    assert "EnvironmentFile=/etc/co-story/worker-release.env" in unit
    assert "EnvironmentFile=/etc/co-story/worker-runtime.env" in unit
    assert "Environment=CO_STORY_RESOLUTION_MODE=async" in unit
    assert "--env-file" in tokens
    assert "/etc/co-story/worker-runtime.env" in tokens
    assert "CO_STORY_RESOLUTION_MODE=${CO_STORY_RESOLUTION_MODE}" in tokens
    assert "--network" in tokens
    assert "host" in tokens
    assert "--read-only" in tokens
    assert tokens[tokens.index("--cap-drop") + 1] == "ALL"
    assert tokens[tokens.index("--security-opt") + 1] == "no-new-privileges"
    assert "--no-healthcheck" in tokens
    assert "--user" in tokens
    assert tokens[tokens.index("--user") + 1] == (
        "${CO_STORY_WORKER_UID}:${CO_STORY_WORKER_GID}"
    )
    assert "--log-driver" in tokens
    assert tokens[tokens.index("--log-driver") + 1] == "awslogs"
    assert "awslogs-group=/co-story/tier2/worker" in tokens
    assert "awslogs-region=${CO_STORY_AWS_REGION}" in tokens
    assert "awslogs-stream=${CO_STORY_WORKER_LOG_STREAM}" in tokens
    assert "python" in tokens
    assert tokens[-2:] == ["-m", "app.workers.story_resolution_worker_bootstrap"]
    assert "co-story-worker" in tokens

    assert "/etc/pki/rds/rds-ca.pem" in unit
    assert "DATABASE_URL=" not in unit
    assert "password" not in unit.lower()
    assert "/etc/co-story/database.env" not in unit
    assert "--publish" not in tokens
    assert "-p" not in tokens
    assert "--privileged" not in tokens
    assert "SendMessage" not in unit
    assert "uvicorn" not in tokens


def test_worker_unit_is_packaged_in_the_scanned_image() -> None:
    dockerfile = _read(DOCKERFILE)

    assert (
        "COPY ops/systemd/co-story-worker-container.service "
        "/usr/local/share/co-story/co-story-worker-container.service"
    ) in dockerfile
    assert (
        "chmod 0444 /usr/local/share/co-story/co-story-worker-container.service"
        in dockerfile
    )


def test_worker_unit_is_private_non_root_and_secret_value_free() -> None:
    _assert_worker_unit_contract(_read(WORKER_UNIT))


@pytest.mark.parametrize(
    "unsafe_change",
    [
        lambda unit: unit.replace("--read-only", ""),
        lambda unit: unit.replace("--network host", "--publish 8000:8000"),
        lambda unit: unit.replace(
            "--env-file /etc/co-story/worker-runtime.env",
            "--env-file /etc/co-story/database.env",
        ),
        lambda unit: unit.replace(
            "python -m app.workers.story_resolution_worker_bootstrap",
            "uvicorn app.main:create_app",
        ),
        lambda unit: unit.replace(
            "Environment=CO_STORY_RESOLUTION_MODE=async",
            "Environment=CO_STORY_RESOLUTION_MODE=sync",
        ),
    ],
    ids=[
        "writable-root",
        "published-port",
        "host-secret-file",
        "web-command",
        "sync-worker",
    ],
)
def test_worker_unit_sensitivity_rejects_boundary_regressions(unsafe_change) -> None:
    unit = _read(WORKER_UNIT)
    with pytest.raises(AssertionError):
        _assert_worker_unit_contract(unsafe_change(unit))
