from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from test_tier3_legacy_bootstrap import (
    NEXT_TARGET,
    TARGET,
    UNIT,
    _events,
    _host_path,
    _run,
    _sandbox,
)


SYNC_ENVIRONMENT = b"Environment=CO_STORY_RESOLUTION_MODE=sync\n"
ASYNC_ENVIRONMENT = b"Environment=CO_STORY_RESOLUTION_MODE=async\n"


def _set_active_unit(host: Path, environment_lines: bytes) -> bytes:
    unit = UNIT.read_bytes()
    assert unit.count(SYNC_ENVIRONMENT) == 1
    unit = unit.replace(SYNC_ENVIRONMENT, environment_lines)
    installed = _host_path(host, "/etc/systemd/system/co-story.service")
    stable = _host_path(
        host, "/usr/local/share/co-story/co-story-container.service"
    )
    installed.write_bytes(unit)
    stable.write_bytes(unit)
    installed.chmod(0o644)
    stable.chmod(0o644)

    state = _host_path(host, "/etc/co-story/container-transition.state")
    lines = state.read_text(encoding="utf-8").splitlines()
    checksum = hashlib.sha256(unit).hexdigest()
    state.write_text(
        "\n".join(
            f"CONTAINER_UNIT_SHA256={checksum}"
            if line.startswith("CONTAINER_UNIT_SHA256=")
            else line
            for line in lines
        )
        + "\n",
        encoding="utf-8",
    )
    return unit


def test_digest_release_preserves_active_async_for_candidate_promotion_and_rollback(
    tmp_path: Path,
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    async_unit = _set_active_unit(host, ASYNC_ENVIRONMENT)
    event_log.write_text("", encoding="utf-8")

    released = _run(
        env,
        "digest-release",
        target=NEXT_TARGET,
        previous=TARGET,
        legacy="",
    )

    assert released.returncode == 0, released.stderr
    events = _events(event_log)
    candidate = next(event for event in events if "--name co-story-candidate" in event)
    assert "--env CO_STORY_RESOLUTION_MODE=async" in candidate
    installed = _host_path(host, "/etc/systemd/system/co-story.service")
    stable = _host_path(
        host, "/usr/local/share/co-story/co-story-container.service"
    )
    assert installed.read_bytes() == stable.read_bytes() == async_unit

    event_log.write_text("", encoding="utf-8")
    env["CO_STORY_TEST_FAIL"] = "target-active"
    failed = _run(
        env,
        "digest-release",
        target="sha256:" + "3" * 64,
        previous=NEXT_TARGET,
        legacy="",
    )

    assert failed.returncode != 0
    assert installed.read_bytes() == stable.read_bytes() == async_unit
    assert "health:previous-restore:8000" in _events(event_log)


@pytest.mark.parametrize(
    "environment_lines",
    (
        b"",
        SYNC_ENVIRONMENT + ASYNC_ENVIRONMENT,
        b"Environment=CO_STORY_RESOLUTION_MODE=\n",
        b"Environment=CO_STORY_RESOLUTION_MODE=ASYNC\n",
        b"Environment=CO_STORY_RESOLUTION_MODE=other\n",
        b"Environment=CO_STORY_RESOLUTION_MODE= async\n",
    ),
    ids=("missing", "duplicate", "empty", "uppercase", "unknown", "whitespace"),
)
def test_digest_release_rejects_noncanonical_active_mode_before_external_or_mutating_work(
    tmp_path: Path, environment_lines: bytes
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    _set_active_unit(host, environment_lines)
    installed_before = _host_path(
        host, "/etc/systemd/system/co-story.service"
    ).read_bytes()
    stable_before = _host_path(
        host, "/usr/local/share/co-story/co-story-container.service"
    ).read_bytes()
    state_before = _host_path(
        host, "/etc/co-story/container-transition.state"
    ).read_bytes()
    event_log.write_text("", encoding="utf-8")

    result = _run(
        env,
        "digest-release",
        target=NEXT_TARGET,
        previous=TARGET,
        legacy="",
    )

    assert result.returncode != 0
    assert "invalid_active_resolution_mode" in result.stderr
    events = _events(event_log)
    assert not any(event.startswith("docker:login") for event in events)
    assert not any(event.startswith("docker:pull") for event in events)
    assert "migration" not in events
    assert not any(event.startswith("mutation:") for event in events)
    assert _host_path(
        host, "/etc/systemd/system/co-story.service"
    ).read_bytes() == installed_before
    assert _host_path(
        host, "/usr/local/share/co-story/co-story-container.service"
    ).read_bytes() == stable_before
    assert _host_path(
        host, "/etc/co-story/container-transition.state"
    ).read_bytes() == state_before
