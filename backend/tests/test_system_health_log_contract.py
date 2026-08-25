import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[2]
WRITER = ROOT / "ops/observability/write_system_health.sh"
SERVICE = ROOT / "ops/systemd/co-story-system-health.service"
TIMER = ROOT / "ops/systemd/co-story-system-health.timer"


def test_system_health_writer_emits_only_fixed_allowlisted_state(tmp_path) -> None:
    fake_systemctl = tmp_path / "systemctl"
    fake_systemctl.write_text(
        "#!/bin/sh\n"
        "case \"$2\" in\n"
        "  co-story.service|amazon-cloudwatch-agent.service|co-story-nginx-public.service) echo active ;;\n"
        "  *) echo 'secret-state'; exit 1 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    fake_systemctl.chmod(0o755)
    output = tmp_path / "system.jsonl"

    subprocess.run(
        [str(WRITER), str(output), str(fake_systemctl)],
        check=True,
        text=True,
        capture_output=True,
    )

    assert json.loads(output.read_text(encoding="utf-8")) == {
        "event_type": "system_health",
        "application": "active",
        "cloudwatch_agent": "active",
        "public_edge": "active",
    }
    assert output.stat().st_mode & 0o777 == 0o640


def test_system_health_writer_rejects_symlink_and_normalizes_unknown_state(tmp_path) -> None:
    fake_systemctl = tmp_path / "systemctl"
    fake_systemctl.write_text("#!/bin/sh\necho 'secret-state'\n", encoding="utf-8")
    fake_systemctl.chmod(0o755)
    real = tmp_path / "real"
    real.write_text("unchanged", encoding="utf-8")
    link = tmp_path / "system.jsonl"
    link.symlink_to(real)

    denied = subprocess.run(
        [str(WRITER), str(link), str(fake_systemctl)],
        text=True,
        capture_output=True,
    )

    assert denied.returncode != 0
    assert real.read_text(encoding="utf-8") == "unchanged"

    output = tmp_path / "normalized.jsonl"
    subprocess.run(
        [str(WRITER), str(output), str(fake_systemctl)],
        check=True,
        text=True,
        capture_output=True,
    )
    assert set(json.loads(output.read_text(encoding="utf-8")).values()) <= {
        "system_health",
        "unknown",
    }


def test_system_health_timer_is_bounded_and_hardened() -> None:
    service = SERVICE.read_text(encoding="utf-8")
    timer = TIMER.read_text(encoding="utf-8")

    assert "Type=oneshot" in service
    assert "ExecStart=/usr/local/libexec/co-story-write-system-health" in service
    assert "ReadWritePaths=/var/log/co-story" in service
    assert "NoNewPrivileges=true" in service
    assert "ProtectSystem=strict" in service
    assert "OnBootSec=1min" in timer
    assert "OnUnitActiveSec=5min" in timer
    assert "Persistent=false" in timer
