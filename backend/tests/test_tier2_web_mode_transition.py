from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "ops/release/transition_web_resolution_mode.sh"
DIGEST = "sha256:" + "a" * 64
IMAGE = (
    "123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/"
    f"co-story-tier3@{DIGEST}"
)
LEGACY = "tier1-20260825-4a51e0e"
DRIVER = b"safe-versioned-deploy-driver\n"


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _unit(mode: str) -> bytes:
    return (
        "[Unit]\n"
        "Description=Co-Story container runtime behind the existing Nginx edge\n"
        "[Service]\n"
        "EnvironmentFile=/etc/co-story/container-release.env\n"
        f"Environment=CO_STORY_RESOLUTION_MODE={mode}\n"
        "ExecStart=/usr/bin/docker run --name co-story "
        "--env CO_STORY_RESOLUTION_MODE=${CO_STORY_RESOLUTION_MODE} "
        "${CO_STORY_CONTAINER_IMAGE}\n"
    ).encode()


def _host_path(host: Path, absolute: str) -> Path:
    return host / absolute.removeprefix("/")


def _write_state(host: Path, unit: bytes, *, state: str = "container-active") -> bytes:
    content = (
        f"STATE={state}\n"
        f"LEGACY_RELEASE_ID={LEGACY}\n"
        f"LEGACY_RELEASE_TARGET=/opt/co-story/releases/{LEGACY}\n"
        f"LEGACY_UNIT_SHA256={'1' * 64}\n"
        f"DRIVER_SHA256={_sha256(DRIVER)}\n"
        f"CONTAINER_UNIT_SHA256={_sha256(unit)}\n"
        f"CONTAINER_IMAGE={IMAGE}\n"
    ).encode()
    path = _host_path(host, "/etc/co-story/container-transition.state")
    path.write_bytes(content)
    path.chmod(0o600)
    return content


def _sandbox(tmp_path: Path) -> tuple[Path, dict[str, str], Path]:
    assert SCRIPT.is_file(), "Web mode transition script 尚未建立"
    host = tmp_path / "host"
    events = tmp_path / "events.log"
    installed = _host_path(host, "/etc/systemd/system/co-story.service")
    stable = _host_path(host, "/usr/local/share/co-story/co-story-container.service")
    driver = _host_path(host, "/usr/local/libexec/co-story-deploy-container")
    release_env = _host_path(host, "/etc/co-story/container-release.env")
    for path in (installed, stable, driver, release_env):
        path.parent.mkdir(parents=True, exist_ok=True)
    sync_unit = _unit("sync")
    installed.write_bytes(sync_unit)
    stable.write_bytes(sync_unit)
    installed.chmod(0o644)
    stable.chmod(0o644)
    driver.write_bytes(DRIVER)
    driver.chmod(0o755)
    release_env.write_text(
        f"CO_STORY_CONTAINER_IMAGE={IMAGE}\n"
        "CO_STORY_CONTAINER_UID=992\n"
        "CO_STORY_CONTAINER_GID=992\n",
        encoding="utf-8",
    )
    release_env.chmod(0o600)
    _write_state(host, sync_unit)
    env = os.environ.copy()
    env.update(
        {
            "CO_STORY_TEST_ROOT": str(host),
            "CO_STORY_TEST_EVENT_LOG": str(events),
            "CO_STORY_TEST_SERVICE_STATE": "active",
            "CO_STORY_TEST_CONTAINER_STATE": "running",
            "CO_STORY_TEST_CONTAINER_RESTARTS": "0",
            "CO_STORY_TEST_CONTAINER_MODE": "sync",
        }
    )
    return host, env, events


def _run(
    env: dict[str, str],
    action: str,
    *,
    digest: str = DIGEST,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), action, digest, "app.example.test"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_versioned_transition_contract_is_bounded_and_secret_free() -> None:
    assert SCRIPT.is_file(), "Web mode transition script 尚未建立"
    script = SCRIPT.read_text(encoding="utf-8")

    assert "web_async_activation=verified previous=sync current=async" in script
    assert "web_async_rollback=verified previous=async current=sync" in script
    assert "web_mode_transition=stopped reason=" in script
    assert "aws " not in script
    assert "docker login" not in script
    assert "--show-error" not in script
    assert "cat \"$runtime_env\"" not in script
    assert "cat \"$database_env\"" not in script
    assert "--name co-story-web-mode-candidate" in script
    assert "--env CO_STORY_RESOLUTION_MODE=$target_mode" in script


def test_activation_atomically_updates_both_units_and_canonical_state(
    tmp_path: Path,
) -> None:
    host, env, events = _sandbox(tmp_path)
    release_before = _host_path(host, "/etc/co-story/container-release.env").read_bytes()

    result = _run(env, "activate")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == (
        "web_async_activation=verified previous=sync current=async"
    )
    installed = _host_path(host, "/etc/systemd/system/co-story.service").read_bytes()
    stable = _host_path(
        host, "/usr/local/share/co-story/co-story-container.service"
    ).read_bytes()
    assert installed == stable == _unit("async")
    state = _host_path(host, "/etc/co-story/container-transition.state").read_text()
    assert "STATE=container-active\n" in state
    assert f"CONTAINER_UNIT_SHA256={_sha256(installed)}\n" in state
    assert f"CONTAINER_IMAGE={IMAGE}\n" in state
    assert _host_path(host, "/etc/co-story/container-release.env").read_bytes() == release_before
    assert not _host_path(host, "/etc/co-story/web-mode-previous-unit").exists()
    assert not _host_path(host, "/etc/co-story/web-mode-previous-state").exists()
    event_lines = events.read_text(encoding="utf-8").splitlines()
    assert event_lines.index("mutation:pending-state") < event_lines.index(
        "mutation:stable-unit"
    )
    assert event_lines.index("mutation:installed-unit") < event_lines.index(
        "service:target-restart"
    )
    assert event_lines.index("service:target-restart") < event_lines.index(
        "health:target:async"
    )


def test_rollback_returns_the_verified_async_state_to_sync(tmp_path: Path) -> None:
    host, env, _events = _sandbox(tmp_path)
    activated = _run(env, "activate")
    assert activated.returncode == 0, activated.stderr
    env["CO_STORY_TEST_CONTAINER_MODE"] = "async"

    rolled_back = _run(env, "rollback")

    assert rolled_back.returncode == 0, rolled_back.stderr
    assert rolled_back.stdout.strip() == (
        "web_async_rollback=verified previous=async current=sync"
    )
    installed = _host_path(host, "/etc/systemd/system/co-story.service").read_bytes()
    stable = _host_path(
        host, "/usr/local/share/co-story/co-story-container.service"
    ).read_bytes()
    assert installed == stable == _unit("sync")
    state = _host_path(host, "/etc/co-story/container-transition.state").read_text()
    assert f"CONTAINER_UNIT_SHA256={_sha256(installed)}\n" in state


@pytest.mark.parametrize(
    "mutation",
    (
        "same-mode",
        "digest-mismatch",
        "unit-drift",
        "state-checksum-drift",
        "existing-backup",
        "service-inactive",
        "restart-count",
    ),
)
def test_preflight_mismatch_is_read_only(tmp_path: Path, mutation: str) -> None:
    host, env, events = _sandbox(tmp_path)
    action = "activate"
    digest = DIGEST
    if mutation == "same-mode":
        action = "rollback"
    elif mutation == "digest-mismatch":
        digest = "sha256:" + "b" * 64
    elif mutation == "unit-drift":
        _host_path(host, "/etc/systemd/system/co-story.service").write_bytes(
            _unit("sync") + b"# drift\n"
        )
    elif mutation == "state-checksum-drift":
        state = _host_path(host, "/etc/co-story/container-transition.state")
        state.write_text(
            state.read_text().replace(
                "CONTAINER_UNIT_SHA256=", "CONTAINER_UNIT_SHA256=" + "0" * 64 + "#"
            ),
            encoding="utf-8",
        )
    elif mutation == "existing-backup":
        _host_path(host, "/etc/co-story/web-mode-previous-unit").write_text("stale")
    elif mutation == "service-inactive":
        env["CO_STORY_TEST_SERVICE_STATE"] = "inactive"
    elif mutation == "restart-count":
        env["CO_STORY_TEST_CONTAINER_RESTARTS"] = "1"
    installed_before = _host_path(host, "/etc/systemd/system/co-story.service").read_bytes()
    stable_before = _host_path(
        host, "/usr/local/share/co-story/co-story-container.service"
    ).read_bytes()
    state_before = _host_path(host, "/etc/co-story/container-transition.state").read_bytes()

    result = _run(env, action, digest=digest)

    assert result.returncode != 0
    assert "web_mode_transition=stopped reason=" in result.stderr
    assert _host_path(host, "/etc/systemd/system/co-story.service").read_bytes() == installed_before
    assert _host_path(
        host, "/usr/local/share/co-story/co-story-container.service"
    ).read_bytes() == stable_before
    assert _host_path(host, "/etc/co-story/container-transition.state").read_bytes() == state_before
    assert not events.exists() or "mutation:" not in events.read_text(encoding="utf-8")


def test_async_candidate_failure_stops_before_live_mutation(tmp_path: Path) -> None:
    host, env, events = _sandbox(tmp_path)
    env["CO_STORY_TEST_FAIL"] = "target-candidate"
    installed = _host_path(host, "/etc/systemd/system/co-story.service")
    stable = _host_path(host, "/usr/local/share/co-story/co-story-container.service")
    state = _host_path(host, "/etc/co-story/container-transition.state")
    installed_before = installed.read_bytes()
    stable_before = stable.read_bytes()
    state_before = state.read_bytes()

    result = _run(env, "activate")

    assert result.returncode == 2
    assert result.stderr.strip() == (
        "web_mode_transition=stopped reason=target_candidate_failed"
    )
    assert installed.read_bytes() == installed_before
    assert stable.read_bytes() == stable_before
    assert state.read_bytes() == state_before
    assert not _host_path(host, "/etc/co-story/web-mode-previous-unit").exists()
    assert not _host_path(host, "/etc/co-story/web-mode-previous-state").exists()
    event_lines = events.read_text(encoding="utf-8").splitlines()
    assert "candidate:async" in event_lines
    assert not any(line.startswith("mutation:") for line in event_lines)


@pytest.mark.parametrize(
    "failure",
    ("target-unit-drift", "target-restart", "target-health", "final-state"),
)
def test_activation_failure_restores_exact_sync_unit_and_state(
    tmp_path: Path, failure: str
) -> None:
    host, env, events = _sandbox(tmp_path)
    env["CO_STORY_TEST_FAIL"] = failure
    installed = _host_path(host, "/etc/systemd/system/co-story.service")
    stable = _host_path(host, "/usr/local/share/co-story/co-story-container.service")
    state = _host_path(host, "/etc/co-story/container-transition.state")
    installed_before = installed.read_bytes()
    state_before = state.read_bytes()

    result = _run(env, "activate")

    assert result.returncode != 0
    assert installed.read_bytes() == stable.read_bytes() == installed_before
    assert state.read_bytes() == state_before
    assert not _host_path(host, "/etc/co-story/web-mode-previous-unit").exists()
    assert not _host_path(host, "/etc/co-story/web-mode-previous-state").exists()
    event_lines = events.read_text(encoding="utf-8").splitlines()
    assert "service:restore-restart" in event_lines
    assert "health:restore:sync" in event_lines


def test_successful_restore_preserves_the_original_failure_reason(tmp_path: Path) -> None:
    _host, env, _events = _sandbox(tmp_path)
    env["CO_STORY_TEST_FAIL"] = "target-health"

    result = _run(env, "activate")

    assert result.returncode == 2
    assert result.stderr.strip() == (
        "web_mode_transition=stopped reason=target_health_failed"
    )


def test_restore_failure_preserves_root_only_forensic_state(tmp_path: Path) -> None:
    host, env, _events = _sandbox(tmp_path)
    env["CO_STORY_TEST_FAIL"] = "target-health,restore-health"

    result = _run(env, "activate")

    assert result.returncode != 0
    state = _host_path(host, "/etc/co-story/container-transition.state")
    assert "STATE=web-mode-restore-failed\n" in state.read_text(encoding="utf-8")
    assert state.stat().st_mode & 0o777 == 0o600
    assert _host_path(host, "/etc/co-story/web-mode-previous-unit").exists()
    assert _host_path(host, "/etc/co-story/web-mode-previous-state").exists()


def test_restore_failure_reports_the_exact_sanitized_phase(tmp_path: Path) -> None:
    _host, env, _events = _sandbox(tmp_path)
    env["CO_STORY_TEST_FAIL"] = "target-health,restore-health"

    result = _run(env, "activate")

    assert result.returncode == 2
    assert result.stderr.strip() == (
        "web_mode_transition=stopped reason=restore_health_failed"
    )


def test_failure_output_never_includes_environment_or_player_content(tmp_path: Path) -> None:
    host, env, _events = _sandbox(tmp_path)
    sensitive = "must-not-appear-in-output"
    _host_path(host, "/etc/co-story/runtime.env").parent.mkdir(
        parents=True, exist_ok=True
    )
    _host_path(host, "/etc/co-story/runtime.env").write_text(sensitive)
    env["CO_STORY_TEST_FAIL"] = "target-health"

    result = _run(env, "activate")

    assert result.returncode != 0
    assert sensitive not in result.stdout
    assert sensitive not in result.stderr
