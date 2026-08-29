from __future__ import annotations

import os
from pathlib import Path
import shlex
import subprocess


ROOT = Path(__file__).parents[2]
DOCKERFILE = ROOT / "Dockerfile"
UNIT = ROOT / "ops/systemd/co-story-publisher-container.service"
INSTALLER = ROOT / "ops/release/install_story_job_publisher.sh"


def _read(path: Path) -> str:
    assert path.is_file(), f"publisher asset 尚未建立：{path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def _execstart_tokens(unit: str) -> list[str]:
    command = next(
        line.removeprefix("ExecStart=")
        for line in unit.splitlines()
        if line.startswith("ExecStart=")
    )
    return shlex.split(command)


def test_publisher_unit_is_packaged_with_bounded_installer() -> None:
    dockerfile = _read(DOCKERFILE)

    assert (
        "COPY ops/systemd/co-story-publisher-container.service "
        "/usr/local/share/co-story/co-story-publisher-container.service"
    ) in dockerfile
    assert (
        "COPY ops/release/install_story_job_publisher.sh "
        "/usr/local/share/co-story/install_story_job_publisher.sh"
    ) in dockerfile
    assert "chmod 0444 /usr/local/share/co-story/co-story-publisher-container.service" in dockerfile
    assert "chmod 0555 /usr/local/share/co-story/install_story_job_publisher.sh" in dockerfile


def test_publisher_unit_runs_on_web_identity_but_requires_separate_activation_file() -> None:
    unit = _read(UNIT)
    tokens = _execstart_tokens(unit)

    assert "ConditionPathExists=/etc/co-story/publisher-runtime.env" in unit
    assert "EnvironmentFile=/etc/co-story/container-release.env" in unit
    assert "EnvironmentFile=/etc/co-story/runtime.env" in unit
    assert "EnvironmentFile=/etc/co-story/database.env" in unit
    assert "EnvironmentFile=/etc/co-story/publisher-runtime.env" in unit
    assert "--read-only" in tokens
    assert tokens[tokens.index("--cap-drop") + 1] == "ALL"
    assert tokens[tokens.index("--security-opt") + 1] == "no-new-privileges"
    assert "--no-healthcheck" in tokens
    assert tokens[tokens.index("--user") + 1] == (
        "${CO_STORY_CONTAINER_UID}:${CO_STORY_CONTAINER_GID}"
    )
    assert tokens[-3:] == ["-m", "app.workers.story_job_publisher"][-3:]
    assert "python" in tokens
    assert "--publish" not in tokens
    assert "-p" not in tokens
    assert "--privileged" not in tokens
    assert "CO_STORY_PUBLISHER_ENABLED=true" not in unit
    assert "Environment=CO_STORY_RESOLUTION_MODE=async" not in unit
    assert "WantedBy=multi-user.target" not in unit


def _installer_harness(tmp_path: Path, *, daemon_reload_status: int = 0):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    events = tmp_path / "events"
    root = tmp_path / "host"
    source = tmp_path / "publisher.service"
    source.write_text("[Service]\n", encoding="utf-8")
    source.chmod(0o400)

    def executable(name: str, body: str) -> None:
        path = fake_bin / name
        path.write_text(f"#!/bin/sh\n{body}", encoding="utf-8")
        path.chmod(0o755)

    executable("id", "printf '0\\n'\n")
    executable(
        "stat",
        "case \"$*\" in *publisher.service*) printf 'root:root:400\\n' ;; "
        "*) /usr/bin/stat \"$@\" ;; esac\n",
    )
    executable(
        "install",
        "for last; do :; done\nmkdir -p \"$(dirname \"$last\")\"\ncp \"$5\" \"$last\"\nchmod 0444 \"$last\"\n",
    )
    executable(
        "systemctl",
        "printf '%s\\n' \"$*\" >>\"$TEST_EVENTS\"\n"
        "case \"$1\" in\n"
        f"  daemon-reload) exit {daemon_reload_status} ;;\n"
        "  is-enabled) printf 'disabled\\n'; exit 1 ;;\n"
        "  is-active) printf 'inactive\\n'; exit 3 ;;\n"
        "  *) exit 91 ;;\n"
        "esac\n",
    )
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": f"{fake_bin}:{environment['PATH']}",
            "CO_STORY_TEST_ROOT": str(root),
            "TEST_EVENTS": str(events),
        }
    )
    result = subprocess.run(
        ["bash", str(INSTALLER), str(source), "install"],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    installed = root / "etc/systemd/system/co-story-publisher.service"
    recorded = events.read_text(encoding="utf-8").splitlines() if events.exists() else []
    return result, installed, recorded


def test_installer_promotes_unit_but_never_enables_or_starts_it(tmp_path) -> None:
    result, installed, events = _installer_harness(tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "publisher_service=installed:disabled"
    assert installed.is_file()
    assert events == [
        "is-active co-story-publisher.service",
        "daemon-reload",
        "is-enabled co-story-publisher.service",
        "is-active co-story-publisher.service",
    ]
    assert not any(
        action in event
        for event in events
        for action in ("enable", "start", "restart")
    )


def test_installer_rolls_back_new_unit_when_daemon_reload_fails(tmp_path) -> None:
    result, installed, events = _installer_harness(tmp_path, daemon_reload_status=1)

    assert result.returncode != 0
    assert result.stdout.strip() == "publisher_service=stopped:daemon_reload_failed"
    assert not installed.exists()
    assert events == [
        "is-active co-story-publisher.service",
        "daemon-reload",
        "daemon-reload",
    ]


def test_installer_source_is_root_owned_regular_read_only_asset() -> None:
    script = _read(INSTALLER)

    assert "root:root:400" in script
    assert "-L \"$unit_source\"" in script
    assert "systemctl enable" not in script
    assert "systemctl start" not in script
    assert "systemctl restart" not in script
