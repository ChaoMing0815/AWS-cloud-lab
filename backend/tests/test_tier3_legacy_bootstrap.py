from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "ops/release/deploy_container.sh"
UNIT = ROOT / "ops/systemd/co-story-container.service"
LEGACY = "tier1-20260825-4a51e0e"
REPOSITORY = "123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/co-story-tier3"
TARGET = "sha256:" + "1" * 64
NEXT_TARGET = "sha256:" + "2" * 64


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _host_path(root: Path, absolute: str) -> Path:
    return root / absolute.removeprefix("/")


def _sandbox(tmp_path: Path) -> tuple[Path, dict[str, str], Path]:
    host = tmp_path / "host"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    events = tmp_path / "events.log"
    legacy_release = _host_path(host, f"/opt/co-story/releases/{LEGACY}")
    legacy_unit = legacy_release / "ops/systemd/co-story.service"
    installed_unit = _host_path(host, "/etc/systemd/system/co-story.service")
    runtime_env = _host_path(host, "/etc/co-story/runtime.env")
    database_env = _host_path(host, "/etc/co-story/database.env")
    current = _host_path(host, "/opt/co-story/current")
    for directory in (
        legacy_unit.parent,
        installed_unit.parent,
        runtime_env.parent,
        _host_path(host, "/var/log/co-story"),
        _host_path(host, "/usr/local/libexec"),
        _host_path(host, "/usr/local/share/co-story"),
    ):
        directory.mkdir(parents=True, exist_ok=True)
    legacy_text = "[Service]\nExecStart=/opt/co-story/current/.venv/bin/uvicorn\n"
    legacy_unit.write_text(legacy_text, encoding="utf-8")
    installed_unit.write_text(legacy_text, encoding="utf-8")
    runtime_env.write_text("safe-runtime-placeholder\n", encoding="utf-8")
    database_env.write_text("safe-database-placeholder\n", encoding="utf-8")
    current.symlink_to(legacy_release)

    _write_executable(fake_bin / "id", "#!/bin/sh\necho 0\n")
    _write_executable(fake_bin / "aws", "#!/bin/sh\nprintf 'test-password\\n'\n")
    _write_executable(
        fake_bin / "docker",
        "#!/bin/sh\nprintf 'docker:%s\\n' \"$*\" >>\"$CO_STORY_TEST_EVENT_LOG\"\n"
        "if [ \"${CO_STORY_TEST_FAIL:-}\" = migration ] && "
        "printf '%s' \"$*\" | grep -q app.commands.migrate; then exit 1; fi\n"
        "exit 0\n",
    )
    _write_executable(
        fake_bin / "systemctl",
        "#!/bin/sh\nprintf 'systemctl:%s\\n' \"$*\" >>\"$CO_STORY_TEST_EVENT_LOG\"\nexit 0\n",
    )
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{fake_bin}:{env['PATH']}",
            "CO_STORY_TEST_ROOT": str(host),
            "CO_STORY_TEST_EVENT_LOG": str(events),
            "CO_STORY_TEST_RUNTIME_METADATA": "root:co-story:640",
            "CO_STORY_TEST_DATABASE_METADATA": "root:co-story:640",
        }
    )
    return host, env, events


def _run(
    env: dict[str, str],
    mode: str,
    target: str = TARGET,
    previous: str = "",
    legacy: str = LEGACY,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "bash",
            str(SCRIPT),
            mode,
            REPOSITORY,
            target,
            previous,
            legacy,
            "localhost",
            str(UNIT),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _events(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _assert_order(events: list[str], markers: tuple[str, ...]) -> None:
    positions = [next(i for i, event in enumerate(events) if marker in event) for marker in markers]
    assert positions == sorted(positions)


def test_legacy_bootstrap_checks_migration_and_candidate_before_switch(tmp_path: Path) -> None:
    host, env, event_log = _sandbox(tmp_path)

    result = _run(env, "legacy-bootstrap")

    assert result.returncode == 0, result.stderr
    events = _events(event_log)
    _assert_order(
        events,
        (
            "health:legacy-preflight:8000",
            f"docker:pull {REPOSITORY}@{TARGET}",
            "app.commands.migrate",
            "health:legacy-post-migration:8000",
            "health:target-candidate:8001",
            "mutation:install-container-unit",
            "health:target-active:8000",
        ),
    )
    state = _host_path(host, "/etc/co-story/container-transition.state").read_text()
    assert "STATE=container-active" in state
    assert f"LEGACY_RELEASE_ID={LEGACY}" in state
    assert f"CONTAINER_IMAGE={REPOSITORY}@{TARGET}" in state


@pytest.mark.parametrize(
    ("previous", "legacy"),
    ((TARGET, LEGACY), ("sha256:" + "f" * 64, LEGACY), ("", "tier1-wrong")),
)
def test_legacy_bootstrap_rejects_fake_previous_and_wrong_legacy(
    tmp_path: Path, previous: str, legacy: str
) -> None:
    host, env, event_log = _sandbox(tmp_path)

    result = _run(env, "legacy-bootstrap", previous=previous, legacy=legacy)

    assert result.returncode != 0
    assert not event_log.exists() or "mutation:" not in event_log.read_text()
    assert not _host_path(host, "/etc/co-story/container-transition.state").exists()


@pytest.mark.parametrize(
    ("mutation", "value"),
    (
        ("runtime", "root:root:600"),
        ("database", "root:root:600"),
        ("state", "STATE=stale\n"),
        ("release_env", "CO_STORY_CONTAINER_IMAGE=invalid\n"),
        ("symlink", "wrong"),
    ),
)
def test_legacy_bootstrap_preflight_mismatch_is_read_only(
    tmp_path: Path, mutation: str, value: str
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    if mutation == "runtime":
        env["CO_STORY_TEST_RUNTIME_METADATA"] = value
    elif mutation == "database":
        env["CO_STORY_TEST_DATABASE_METADATA"] = value
    elif mutation == "state":
        _host_path(host, "/etc/co-story/container-transition.state").write_text(value)
    elif mutation == "release_env":
        _host_path(host, "/etc/co-story/container-release.env").write_text(value)
    else:
        current = _host_path(host, "/opt/co-story/current")
        current.unlink()
        current.symlink_to(_host_path(host, "/opt/co-story/releases/wrong"))

    result = _run(env, "legacy-bootstrap")

    assert result.returncode != 0
    assert not event_log.exists() or "mutation:" not in event_log.read_text()


@pytest.mark.parametrize(
    "failure",
    ("migration", "legacy-post-migration", "target-candidate"),
)
def test_bootstrap_failure_before_switch_keeps_legacy_unit(
    tmp_path: Path, failure: str
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    original = _host_path(host, "/etc/systemd/system/co-story.service").read_text()
    env["CO_STORY_TEST_FAIL"] = failure

    result = _run(env, "legacy-bootstrap")

    assert result.returncode != 0
    assert _host_path(host, "/etc/systemd/system/co-story.service").read_text() == original
    assert "mutation:install-container-unit" not in _events(event_log)


def test_target_failure_restores_legacy_and_restore_failure_is_nonzero(tmp_path: Path) -> None:
    host, env, event_log = _sandbox(tmp_path)
    original = _host_path(host, "/etc/systemd/system/co-story.service").read_text()
    env["CO_STORY_TEST_FAIL"] = "target-active"
    result = _run(env, "legacy-bootstrap")
    assert result.returncode != 0
    assert _host_path(host, "/etc/systemd/system/co-story.service").read_text() == original
    assert "health:legacy-restore:8000" in _events(event_log)

    host, env, event_log = _sandbox(tmp_path / "restore-fail")
    env["CO_STORY_TEST_FAIL"] = "target-and-legacy-restore"
    result = _run(env, "legacy-bootstrap")
    assert result.returncode != 0
    state = _host_path(host, "/etc/co-story/container-transition.state").read_text()
    assert "STATE=legacy-restore-failed" in state


def test_digest_release_fences_state_and_restores_previous_digest(tmp_path: Path) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    event_log.write_text("", encoding="utf-8")

    result = _run(
        env,
        "digest-release",
        target=NEXT_TARGET,
        previous=TARGET,
        legacy="",
    )
    assert result.returncode == 0, result.stderr
    _assert_order(
        _events(event_log),
        (
            "app.commands.migrate",
            "health:previous-post-migration:8000",
            "health:target-candidate:8001",
            "health:target-active:8000",
        ),
    )

    event_log.write_text("", encoding="utf-8")
    env["CO_STORY_TEST_FAIL"] = "target-active"
    third = "sha256:" + "3" * 64
    failed = _run(env, "digest-release", target=third, previous=NEXT_TARGET, legacy="")
    assert failed.returncode != 0
    assert "health:previous-restore:8000" in _events(event_log)
    release_env = _host_path(host, "/etc/co-story/container-release.env").read_text()
    assert NEXT_TARGET in release_env

    env.pop("CO_STORY_TEST_FAIL")
    env["CO_STORY_TEST_STALE_FENCE"] = "unit"
    stale = _run(env, "digest-release", target=third, previous=NEXT_TARGET, legacy="")
    assert stale.returncode != 0


def test_manual_legacy_rollback_checks_candidate_and_restores_container_on_failure(
    tmp_path: Path,
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    event_log.write_text("", encoding="utf-8")

    env["CO_STORY_TEST_FAIL"] = "legacy-candidate"
    rejected = _run(env, "legacy-rollback")
    assert rejected.returncode != 0
    assert "mutation:install-legacy-unit" not in _events(event_log)

    env.pop("CO_STORY_TEST_FAIL")
    event_log.write_text("", encoding="utf-8")
    rolled_back = _run(env, "legacy-rollback")
    assert rolled_back.returncode == 0, rolled_back.stderr
    assert "STATE=legacy-active" in _host_path(
        host, "/etc/co-story/container-transition.state"
    ).read_text()

    host, env, event_log = _sandbox(tmp_path / "legacy-target-fail")
    assert _run(env, "legacy-bootstrap").returncode == 0
    event_log.write_text("", encoding="utf-8")
    env["CO_STORY_TEST_FAIL"] = "legacy-target"
    failed = _run(env, "legacy-rollback")
    assert failed.returncode != 0
    assert "health:container-restore:8000" in _events(event_log)
