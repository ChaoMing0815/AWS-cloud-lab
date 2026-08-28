from __future__ import annotations

import os
import hashlib
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
    fake_bin.mkdir(parents=True)
    events = tmp_path / "events.log"
    legacy_release = _host_path(host, f"/opt/co-story/releases/{LEGACY}")
    legacy_unit = legacy_release / "ops/systemd/co-story.service"
    installed_unit = _host_path(host, "/etc/systemd/system/co-story.service")
    runtime_env = _host_path(host, "/etc/co-story/runtime.env")
    database_env = _host_path(host, "/etc/co-story/database.env")
    rds_ca = _host_path(host, "/etc/pki/rds/rds-ca.pem")
    candidate_log = _host_path(host, "/var/log/co-story/candidate.jsonl")
    current = _host_path(host, "/opt/co-story/current")
    for directory in (
        legacy_unit.parent,
        installed_unit.parent,
        runtime_env.parent,
        rds_ca.parent,
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
    rds_ca.write_text("safe-ca-placeholder\n", encoding="utf-8")
    rds_ca.chmod(0o644)
    candidate_log.write_text("", encoding="utf-8")
    candidate_log.chmod(0o640)
    candidate_log.parent.chmod(0o750)
    current.symlink_to(legacy_release)

    _write_executable(
        fake_bin / "id",
        "#!/bin/sh\n"
        "case \"$*\" in\n"
        "  -u) echo 0 ;;\n"
        "  '-u co-story') printf '%s\\n' \"${CO_STORY_TEST_RUNTIME_UID-992}\" ;;\n"
        "  '-g co-story') printf '%s\\n' \"${CO_STORY_TEST_RUNTIME_GID-992}\" ;;\n"
        "  *) exit 1 ;;\n"
        "esac\n",
    )
    _write_executable(fake_bin / "aws", "#!/bin/sh\nprintf 'test-password\\n'\n")
    _write_executable(
        fake_bin / "docker",
        "#!/bin/sh\nprintf 'docker:%s\\n' \"$*\" >>\"$CO_STORY_TEST_EVENT_LOG\"\n"
        "if [ \"${1:-}\" = login ]; then cat >/dev/null; fi\n"
        "if [ \"${1:-}\" = inspect ]; then printf '%s\\n' "
        "\"${CO_STORY_TEST_CANDIDATE_INSPECT:-exited 13}\"; fi\n"
        "if [ \"${CO_STORY_TEST_FAIL:-}\" = migration ] && "
        "printf '%s' \"$*\" | grep -q app.commands.migrate; then exit 1; fi\n"
        "exit 0\n",
    )
    _write_executable(
        fake_bin / "systemctl",
        "#!/bin/sh\nprintf 'systemctl:%s\\n' \"$*\" >>\"$CO_STORY_TEST_EVENT_LOG\"\n"
        "if [ \"$*\" = 'restart co-story.service' ]; then\n"
        "  installed=\"$CO_STORY_TEST_ROOT/etc/systemd/system/co-story.service\"\n"
        "  stable=\"$CO_STORY_TEST_ROOT/usr/local/share/co-story/co-story-container.service\"\n"
        "  installed_sha=$(shasum -a 256 \"$installed\" | awk '{print $1}')\n"
        "  if [ -f \"$stable\" ]; then\n"
        "    stable_sha=$(shasum -a 256 \"$stable\" | awk '{print $1}')\n"
        "  else\n"
        "    stable_sha=missing\n"
        "  fi\n"
        "  printf 'restart-unit:installed=%s stable=%s\\n' \"$installed_sha\" \"$stable_sha\" >>\"$CO_STORY_TEST_EVENT_LOG\"\n"
        "fi\n"
        "if [ \"$*\" = 'is-active --quiet co-story-legacy-candidate.service' ]; then exit 3; fi\n"
        "exit 0\n",
    )
    _write_executable(
        fake_bin / "systemd-run",
        "#!/bin/sh\nprintf 'systemd-run:%s\\n' \"$*\" >>\"$CO_STORY_TEST_EVENT_LOG\"\nexit 0\n",
    )
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{fake_bin}:{env['PATH']}",
            "CO_STORY_TEST_ROOT": str(host),
            "CO_STORY_TEST_EVENT_LOG": str(events),
            "CO_STORY_TEST_RUNTIME_METADATA": "root:co-story:640",
            "CO_STORY_TEST_DATABASE_METADATA": "root:co-story:640",
            "CO_STORY_TEST_CA_METADATA": "root:root:644",
            "CO_STORY_TEST_RUNTIME_UID": "992",
            "CO_STORY_TEST_RUNTIME_GID": "992",
            "CO_STORY_TEST_LOG_DIR_METADATA": "992:992:750",
            "CO_STORY_TEST_CANDIDATE_LOG_METADATA": "992:992:640",
            "CO_STORY_TEST_RELEASE_METADATA": "root:root:600",
            "CO_STORY_TEST_LOG_WRITABLE": "yes",
        }
    )
    return host, env, events


def _run(
    env: dict[str, str],
    mode: str,
    target: str = TARGET,
    previous: str = "",
    legacy: str = LEGACY,
    unit_asset: Path = UNIT,
    driver_asset: Path = SCRIPT,
    action: str = "release",
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
            str(unit_asset),
            str(driver_asset),
            action,
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


def _unit_without_resolution_mode(tmp_path: Path) -> Path:
    old_unit = tmp_path / "old-container.service"
    target_unit = UNIT.read_text(encoding="utf-8")
    resolution_mode = "Environment=CO_STORY_RESOLUTION_MODE=sync\n"
    assert resolution_mode in target_unit
    old_unit.write_text(target_unit.replace(resolution_mode, ""), encoding="utf-8")
    old_unit.chmod(0o644)
    return old_unit


def _target_unit_with_sync(tmp_path: Path) -> Path:
    target_unit = tmp_path / "target-container.service"
    target_unit.write_bytes(UNIT.read_bytes())
    target_unit.chmod(0o644)
    assert b"Environment=CO_STORY_RESOLUTION_MODE=sync\n" in target_unit.read_bytes()
    return target_unit


def _restart_unit_events(events: list[str]) -> list[str]:
    return [event for event in events if event.startswith("restart-unit:")]


def test_migration_bridge_handoffs_target_unit_before_first_target_restart(
    tmp_path: Path,
) -> None:
    _host, env, event_log = _sandbox(tmp_path)
    old_unit = _unit_without_resolution_mode(tmp_path)
    target_unit = _target_unit_with_sync(tmp_path)
    assert _run(env, "legacy-bootstrap", unit_asset=old_unit).returncode == 0
    event_log.write_text("", encoding="utf-8")

    released = _run(
        env,
        "migration-bridge",
        target=NEXT_TARGET,
        previous=TARGET,
        legacy="",
        unit_asset=target_unit,
    )

    assert released.returncode == 0, released.stderr
    target_sha = hashlib.sha256(target_unit.read_bytes()).hexdigest()
    old_sha = hashlib.sha256(old_unit.read_bytes()).hexdigest()
    restart_units = _restart_unit_events(_events(event_log))
    assert restart_units[0] == f"restart-unit:installed={target_sha} stable={old_sha}"
    assert restart_units[1] == f"restart-unit:installed={target_sha} stable={target_sha}"
    assert "--env CO_STORY_RESOLUTION_MODE=sync" in "\n".join(_events(event_log))
    assert "app.commands.migrate" not in "\n".join(_events(event_log))


@pytest.mark.parametrize("failure", ("bridge-target-unit-install", "bridge-target-daemon-reload"))
def test_migration_bridge_target_unit_prepare_failure_restores_previous_assets(
    tmp_path: Path, failure: str
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    old_unit = _unit_without_resolution_mode(tmp_path)
    target_unit = _target_unit_with_sync(tmp_path)
    assert _run(env, "legacy-bootstrap", unit_asset=old_unit).returncode == 0
    old_driver = _host_path(host, "/usr/local/libexec/co-story-deploy-container").read_bytes()
    env["CO_STORY_TEST_FAIL"] = failure
    event_log.write_text("", encoding="utf-8")

    failed = _run(
        env,
        "migration-bridge",
        target=NEXT_TARGET,
        previous=TARGET,
        legacy="",
        unit_asset=target_unit,
    )

    assert failed.returncode != 0
    assert not _host_path(host, "/etc/co-story/migration-bridge.state").exists()
    assert _host_path(host, "/etc/systemd/system/co-story.service").read_bytes() == old_unit.read_bytes()
    assert _host_path(host, "/usr/local/share/co-story/co-story-container.service").read_bytes() == old_unit.read_bytes()
    assert _host_path(host, "/usr/local/libexec/co-story-deploy-container").read_bytes() == old_driver
    assert TARGET in _host_path(host, "/etc/co-story/container-release.env").read_text()
    assert "health:previous-restore:8000" in _events(event_log)


@pytest.mark.parametrize(
    "stale_fence", ("bridge-target-unit-source", "bridge-target-unit-destination")
)
def test_migration_bridge_target_unit_hash_mismatch_restores_previous_assets(
    tmp_path: Path, stale_fence: str
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    old_unit = _unit_without_resolution_mode(tmp_path)
    target_unit = _target_unit_with_sync(tmp_path)
    assert _run(env, "legacy-bootstrap", unit_asset=old_unit).returncode == 0
    env["CO_STORY_TEST_STALE_FENCE"] = stale_fence
    event_log.write_text("", encoding="utf-8")

    failed = _run(
        env,
        "migration-bridge",
        target=NEXT_TARGET,
        previous=TARGET,
        legacy="",
        unit_asset=target_unit,
    )

    assert failed.returncode != 0
    assert not _host_path(host, "/etc/co-story/migration-bridge.state").exists()
    assert _host_path(host, "/etc/systemd/system/co-story.service").read_bytes() == old_unit.read_bytes()
    assert _host_path(host, "/usr/local/share/co-story/co-story-container.service").read_bytes() == old_unit.read_bytes()
    assert TARGET in _host_path(host, "/etc/co-story/container-release.env").read_text()
    assert "health:previous-restore:8000" in _events(event_log)


def test_migration_bridge_never_runs_migration_and_marks_verified_digest(tmp_path: Path) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    event_log.write_text("", encoding="utf-8")

    result = _run(env, "migration-bridge", target=NEXT_TARGET, previous=TARGET, legacy="")

    assert result.returncode == 0, result.stderr
    assert f"container_release=verified mode=migration-bridge image_digest={NEXT_TARGET}" in result.stdout
    events = _events(event_log)
    assert "app.commands.migrate" not in "\n".join(events)
    marker = _host_path(host, "/etc/co-story/migration-bridge.state").read_text()
    assert marker == "STATE=verified-bridge\n" f"BRIDGE_IMAGE={REPOSITORY}@{NEXT_TARGET}\n"


def test_migration_bridge_target_failure_restores_previous_without_verified_marker(
    tmp_path: Path,
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    event_log.write_text("", encoding="utf-8")
    env["CO_STORY_TEST_FAIL"] = "target-active"

    failed = _run(env, "migration-bridge", target=NEXT_TARGET, previous=TARGET, legacy="")

    assert failed.returncode != 0
    assert not _host_path(host, "/etc/co-story/migration-bridge.state").exists()
    assert TARGET in _host_path(host, "/etc/co-story/container-release.env").read_text()
    assert "health:previous-restore:8000" in _events(event_log)


def test_schema_activation_reports_its_actual_release_mode(tmp_path: Path) -> None:
    _host, env, _event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    assert _run(env, "migration-bridge", target=NEXT_TARGET, previous=TARGET, legacy="").returncode == 0
    third = "sha256:" + "3" * 64

    result = _run(env, "schema-activation", target=third, previous=NEXT_TARGET, legacy="")

    assert result.returncode == 0, result.stderr
    assert f"container_release=verified mode=schema-activation image_digest={third}" in result.stdout
    assert "mode=digest-release" not in result.stdout


def test_schema_activation_rejects_missing_or_stale_bridge_marker_before_migration(tmp_path: Path) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    event_log.write_text("", encoding="utf-8")

    missing = _run(env, "schema-activation", target=NEXT_TARGET, previous=TARGET, legacy="")

    assert missing.returncode != 0
    assert "app.commands.migrate" not in "\n".join(_events(event_log))

    marker = _host_path(host, "/etc/co-story/migration-bridge.state")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        "STATE=verified-bridge\n" f"BRIDGE_IMAGE={REPOSITORY}@{'sha256:' + 'f' * 64}\n",
        encoding="utf-8",
    )
    stale = _run(env, "schema-activation", target=NEXT_TARGET, previous=TARGET, legacy="")

    assert stale.returncode != 0
    assert "app.commands.migrate" not in "\n".join(_events(event_log))


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
    ca_mount = (
        f"type=bind,src={_host_path(host, '/etc/pki/rds/rds-ca.pem')},"
        "dst=/etc/pki/rds/rds-ca.pem,readonly"
    )
    migration = next(event for event in events if "app.commands.migrate" in event)
    candidate = next(event for event in events if "--name co-story-candidate" in event)
    assert ca_mount in migration
    assert ca_mount in candidate
    assert "--user 992:992" in candidate
    assert _host_path(host, "/etc/co-story/container-release.env").read_text() == (
        f"CO_STORY_CONTAINER_IMAGE={REPOSITORY}@{TARGET}\n"
        "CO_STORY_CONTAINER_UID=992\n"
        "CO_STORY_CONTAINER_GID=992\n"
    )


@pytest.mark.parametrize(
    ("uid", "gid"),
    (("0", "992"), ("992", "0"), ("not-numeric", "992"), ("", "992")),
)
def test_invalid_host_runtime_identity_stops_before_candidate_or_mutation(
    tmp_path: Path, uid: str, gid: str
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    env["CO_STORY_TEST_RUNTIME_UID"] = uid
    env["CO_STORY_TEST_RUNTIME_GID"] = gid

    result = _run(env, "legacy-bootstrap")

    assert result.returncode != 0
    events = _events(event_log)
    assert not any("--name co-story-candidate" in event for event in events)
    assert not any(event.startswith("mutation:") for event in events)
    assert not _host_path(host, "/etc/co-story/container-release.env").exists()


@pytest.mark.parametrize(
    ("failure", "metadata"),
    (
        ("directory-owner", "10001:992:750"),
        ("directory-mode", "992:992:770"),
        ("candidate-owner", "10001:992:640"),
        ("candidate-mode", "992:992:660"),
        ("candidate-symlink", "992:992:640"),
        ("not-writable", "992:992:640"),
    ),
)
def test_candidate_log_guard_stops_before_candidate_or_release_mutation(
    tmp_path: Path, failure: str, metadata: str
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    candidate_log = _host_path(host, "/var/log/co-story/candidate.jsonl")
    if failure.startswith("directory"):
        env["CO_STORY_TEST_LOG_DIR_METADATA"] = metadata
    elif failure == "candidate-symlink":
        target = candidate_log.with_name("candidate-target.jsonl")
        target.write_text("", encoding="utf-8")
        candidate_log.unlink()
        candidate_log.symlink_to(target)
    elif failure == "not-writable":
        env["CO_STORY_TEST_LOG_WRITABLE"] = "no"
    else:
        env["CO_STORY_TEST_CANDIDATE_LOG_METADATA"] = metadata

    result = _run(env, "legacy-bootstrap")

    assert result.returncode != 0
    events = _events(event_log)
    assert not any("--name co-story-candidate" in event for event in events)
    assert not any(event.startswith("mutation:") for event in events)
    assert not _host_path(host, "/etc/co-story/container-release.env").exists()


@pytest.mark.parametrize(
    ("ca_failure", "metadata"),
    (
        ("missing", "root:root:644"),
        ("directory", "root:root:644"),
        ("symlink", "root:root:644"),
        ("owner", "co-story:co-story:644"),
        ("group-writable", "root:root:664"),
        ("other-writable", "root:root:646"),
        ("app-unreadable", "root:root:640"),
    ),
)
def test_host_ca_preflight_failure_is_read_only_before_registry_or_pull(
    tmp_path: Path, ca_failure: str, metadata: str
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    ca = _host_path(host, "/etc/pki/rds/rds-ca.pem")
    original_unit = _host_path(host, "/etc/systemd/system/co-story.service").read_bytes()
    if ca_failure == "missing":
        ca.unlink()
    elif ca_failure == "directory":
        ca.unlink()
        ca.mkdir()
    elif ca_failure == "symlink":
        target = ca.with_name("trusted-ca.pem")
        target.write_text("safe-ca-placeholder\n", encoding="utf-8")
        ca.unlink()
        ca.symlink_to(target)
    else:
        env["CO_STORY_TEST_CA_METADATA"] = metadata

    result = _run(env, "legacy-bootstrap")

    assert result.returncode != 0
    events = _events(event_log)
    assert not any(event.startswith("docker:") for event in events)
    assert "migration" not in events
    assert not any(event.startswith("mutation:") for event in events)
    assert _host_path(host, "/etc/systemd/system/co-story.service").read_bytes() == (
        original_unit
    )
    for residual in (
        "/etc/co-story/container-transition.state",
        "/etc/co-story/container-release.env",
        "/etc/co-story/legacy-co-story.service",
        "/usr/local/libexec/co-story-deploy-container",
        "/usr/local/share/co-story/co-story-container.service",
    ):
        assert not _host_path(host, residual).exists()


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


def test_candidate_failure_emits_only_sanitized_state_before_cleanup(tmp_path: Path) -> None:
    _, env, event_log = _sandbox(tmp_path)
    env["CO_STORY_TEST_FAIL"] = "target-candidate"
    env["CO_STORY_TEST_CANDIDATE_INSPECT"] = "exited 13"

    result = _run(env, "legacy-bootstrap")

    assert result.returncode != 0
    assert "container_candidate=unhealthy status=exited exit_code=13" in result.stderr
    assert REPOSITORY not in result.stderr
    assert "safe-runtime-placeholder" not in result.stderr
    events = _events(event_log)
    inspect = next(i for i, event in enumerate(events) if "docker:inspect" in event)
    cleanup = next(
        i
        for i, event in enumerate(events[inspect + 1 :], start=inspect + 1)
        if "docker:rm -f co-story-candidate" in event
    )
    assert inspect < cleanup


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
    assert "STATE=legacy-mutation-restore-failed" in state


def test_target_restart_failure_restores_legacy(tmp_path: Path) -> None:
    host, env, event_log = _sandbox(tmp_path)
    original = _host_path(host, "/etc/systemd/system/co-story.service").read_text()
    env["CO_STORY_TEST_FAIL"] = "target-restart"

    result = _run(env, "legacy-bootstrap")

    assert result.returncode != 0
    assert _host_path(host, "/etc/systemd/system/co-story.service").read_text() == original
    assert "health:legacy-restore:8000" in _events(event_log)


@pytest.mark.parametrize(
    "failure",
    (
        "stable-driver-install",
        "state-write",
        "release-env-write",
        "container-unit-install",
        "daemon-reload",
    ),
)
def test_bootstrap_mutation_failure_restores_clean_retryable_legacy(
    tmp_path: Path, failure: str
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    installed = _host_path(host, "/etc/systemd/system/co-story.service")
    original = installed.read_bytes()
    env["CO_STORY_TEST_FAIL"] = failure

    failed = _run(env, "legacy-bootstrap")

    assert failed.returncode != 0
    assert installed.read_bytes() == original
    assert "health:legacy-restore:8000" in _events(event_log)
    for path in (
        "/etc/co-story/container-transition.state",
        "/etc/co-story/container-release.env",
        "/etc/co-story/legacy-co-story.service",
        "/usr/local/libexec/co-story-deploy-container",
        "/usr/local/share/co-story/co-story-container.service",
    ):
        assert not _host_path(host, path).exists(), path

    env.pop("CO_STORY_TEST_FAIL")
    event_log.write_text("", encoding="utf-8")
    retried = _run(env, "legacy-bootstrap")
    assert retried.returncode == 0, retried.stderr


def test_bootstrap_mutation_restore_failure_is_root_only_and_fail_closed(
    tmp_path: Path,
) -> None:
    host, env, _ = _sandbox(tmp_path)
    env["CO_STORY_TEST_FAIL"] = "stable-driver-install,legacy-restore"

    failed = _run(env, "legacy-bootstrap")

    assert failed.returncode != 0
    state = _host_path(host, "/etc/co-story/container-transition.state")
    assert "STATE=legacy-mutation-restore-failed" in state.read_text()
    assert state.stat().st_mode & 0o777 == 0o600
    env.pop("CO_STORY_TEST_FAIL")
    retry = _run(env, "legacy-bootstrap")
    assert retry.returncode != 0
    assert "existing_transition_state" in retry.stderr


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


@pytest.mark.parametrize(
    ("release_content", "reason"),
    (
        (f"CO_STORY_CONTAINER_IMAGE={REPOSITORY}@{TARGET}\n", "invalid_release_env_shape"),
        (
            f"CO_STORY_CONTAINER_IMAGE={REPOSITORY}@{TARGET}\n"
            "CO_STORY_CONTAINER_UID=0\nCO_STORY_CONTAINER_GID=992\n",
            "invalid_release_env_identity",
        ),
        (
            f"CO_STORY_CONTAINER_IMAGE={REPOSITORY}@{TARGET}\n"
            "CO_STORY_CONTAINER_UID=992\nCO_STORY_CONTAINER_UID=992\n"
            "CO_STORY_CONTAINER_GID=992\n",
            "invalid_release_env_shape",
        ),
        (
            f"CO_STORY_CONTAINER_IMAGE={REPOSITORY}@{TARGET}\n"
            "CO_STORY_CONTAINER_UID=10001\nCO_STORY_CONTAINER_GID=10001\n",
            "release_env_identity_mismatch",
        ),
    ),
)
def test_digest_release_rejects_invalid_root_only_runtime_identity_env(
    tmp_path: Path, release_content: str, reason: str
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    _host_path(host, "/etc/co-story/container-release.env").write_text(
        release_content, encoding="utf-8"
    )
    event_log.write_text("", encoding="utf-8")

    result = _run(
        env, "digest-release", target=NEXT_TARGET, previous=TARGET, legacy=""
    )

    assert result.returncode != 0
    assert reason in result.stderr
    assert "migration" not in _events(event_log)
    assert not any(event.startswith("mutation:") for event in _events(event_log))


def test_legacy_rollback_rejects_missing_runtime_identity_before_candidate(
    tmp_path: Path,
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    _host_path(host, "/etc/co-story/container-release.env").write_text(
        f"CO_STORY_CONTAINER_IMAGE={REPOSITORY}@{TARGET}\n", encoding="utf-8"
    )
    event_log.write_text("", encoding="utf-8")

    result = _run(env, "legacy-rollback")

    assert result.returncode != 0
    assert "invalid_release_env_shape" in result.stderr
    assert not any(event.startswith("systemd-run:") for event in _events(event_log))


def test_digest_release_promotes_target_bound_assets_only_after_target_health(
    tmp_path: Path,
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    new_driver = tmp_path / "target-deploy-container.sh"
    new_driver.write_bytes(SCRIPT.read_bytes() + b"\n# target-driver-version\n")
    new_driver.chmod(0o755)
    new_unit = tmp_path / "target-container.service"
    new_unit.write_bytes(UNIT.read_bytes() + b"\n# target-unit-version\n")
    event_log.write_text("", encoding="utf-8")

    released = _run(
        env,
        "digest-release",
        target=NEXT_TARGET,
        previous=TARGET,
        legacy="",
        unit_asset=new_unit,
        driver_asset=new_driver,
    )

    assert released.returncode == 0, released.stderr
    events = _events(event_log)
    _assert_order(
        events,
        (
            "health:target-active:8000",
            "mutation:promote-stable-assets",
            "health:target-promoted:8000",
        ),
    )
    stable_driver = _host_path(host, "/usr/local/libexec/co-story-deploy-container")
    stable_unit = _host_path(host, "/usr/local/share/co-story/co-story-container.service")
    installed_unit = _host_path(host, "/etc/systemd/system/co-story.service")
    assert stable_driver.read_bytes() == new_driver.read_bytes()
    assert stable_unit.read_bytes() == new_unit.read_bytes()
    assert installed_unit.read_bytes() == new_unit.read_bytes()
    state = _host_path(host, "/etc/co-story/container-transition.state").read_text()
    assert f"DRIVER_SHA256={hashlib.sha256(new_driver.read_bytes()).hexdigest()}" in state


def test_digest_asset_promotion_failure_restores_previous_assets_and_digest(
    tmp_path: Path,
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    stable_driver = _host_path(host, "/usr/local/libexec/co-story-deploy-container")
    stable_unit = _host_path(host, "/usr/local/share/co-story/co-story-container.service")
    old_driver = stable_driver.read_bytes()
    old_unit = stable_unit.read_bytes()
    new_driver = tmp_path / "target-deploy-container.sh"
    new_driver.write_bytes(SCRIPT.read_bytes() + b"\n# unsafe-unverified-promotion\n")
    new_driver.chmod(0o755)
    new_unit = tmp_path / "target-container.service"
    new_unit.write_bytes(UNIT.read_bytes() + b"\n# unsafe-unverified-promotion\n")
    env["CO_STORY_TEST_FAIL"] = "asset-promotion"
    event_log.write_text("", encoding="utf-8")

    failed = _run(
        env,
        "digest-release",
        target=NEXT_TARGET,
        previous=TARGET,
        legacy="",
        unit_asset=new_unit,
        driver_asset=new_driver,
    )

    assert failed.returncode != 0
    assert stable_driver.read_bytes() == old_driver
    assert stable_unit.read_bytes() == old_unit
    assert _host_path(host, "/etc/systemd/system/co-story.service").read_bytes() == old_unit
    assert TARGET in _host_path(host, "/etc/co-story/container-release.env").read_text()
    assert "health:previous-restore:8000" in _events(event_log)


def test_digest_asset_restore_failure_is_root_only_and_fail_closed(tmp_path: Path) -> None:
    host, env, _ = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    new_driver = tmp_path / "target-deploy-container.sh"
    new_driver.write_bytes(SCRIPT.read_bytes() + b"\n# target-driver-version\n")
    new_driver.chmod(0o755)
    new_unit = tmp_path / "target-container.service"
    new_unit.write_bytes(UNIT.read_bytes() + b"\n# target-unit-version\n")
    env["CO_STORY_TEST_FAIL"] = "asset-promotion,previous-restore"

    failed = _run(
        env,
        "digest-release",
        target=NEXT_TARGET,
        previous=TARGET,
        legacy="",
        unit_asset=new_unit,
        driver_asset=new_driver,
    )

    assert failed.returncode != 0
    state = _host_path(host, "/etc/co-story/container-transition.state")
    assert "STATE=asset-restore-failed" in state.read_text()
    assert state.stat().st_mode & 0o777 == 0o600
    assert _host_path(host, "/etc/co-story/previous-stable-driver").exists()
    assert _host_path(host, "/etc/co-story/previous-stable-unit").exists()


@pytest.mark.parametrize(
    "mismatch", ("state", "checksum", "driver", "env", "previous")
)
def test_digest_release_preflight_mismatch_stops_before_migration(
    tmp_path: Path, mismatch: str
) -> None:
    host, env, event_log = _sandbox(tmp_path)
    assert _run(env, "legacy-bootstrap").returncode == 0
    state = _host_path(host, "/etc/co-story/container-transition.state")
    release_env = _host_path(host, "/etc/co-story/container-release.env")
    previous = TARGET
    if mismatch == "state":
        state.write_text(state.read_text().replace("STATE=container-active", "STATE=stale"))
    elif mismatch == "checksum":
        state.write_text(
            state.read_text().replace(
                next(
                    line
                    for line in state.read_text().splitlines()
                    if line.startswith("CONTAINER_UNIT_SHA256=")
                ),
                "CONTAINER_UNIT_SHA256=" + "0" * 64,
            )
        )
    elif mismatch == "driver":
        _host_path(host, "/usr/local/libexec/co-story-deploy-container").write_text(
            "stale driver\n"
        )
    elif mismatch == "env":
        release_env.write_text("CO_STORY_CONTAINER_IMAGE=invalid\n")
    else:
        previous = "sha256:" + "9" * 64
    event_log.write_text("", encoding="utf-8")

    result = _run(
        env,
        "digest-release",
        target=NEXT_TARGET,
        previous=previous,
        legacy="",
    )

    assert result.returncode != 0
    assert "migration" not in _events(event_log)
    assert not any(event.startswith("mutation:") for event in _events(event_log))


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
    events = _events(event_log)
    legacy_driver = f"/opt/co-story/releases/{LEGACY}/.venv/bin/uvicorn"
    _assert_order(events, (f"systemd-run:", legacy_driver, "health:legacy-candidate:8001"))
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
