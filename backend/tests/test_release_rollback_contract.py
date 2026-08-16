from pathlib import Path


ROOT = Path(__file__).parents[2]
ACTIVATE_SCRIPT = ROOT / "ops/release/activate.sh"
ROLLBACK_SCRIPT = ROOT / "ops/release/rollback.sh"
MIGRATION_UNIT = ROOT / "ops/systemd/co-story-migrate@.service"
CANDIDATE_UNIT = ROOT / "ops/systemd/co-story-candidate@.service"


def _read(path: Path) -> str:
    assert path.is_file(), f"release asset 尚未建立：{path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def test_release_assets_keep_migration_and_candidate_checks_outside_main_service() -> None:
    migration = _read(MIGRATION_UNIT)
    candidate = _read(CANDIDATE_UNIT)

    assert "Type=oneshot" in migration
    assert "User=co-story" in migration
    assert "EnvironmentFile=/etc/co-story/runtime.env" in migration
    assert "EnvironmentFile=/etc/co-story/database.env" in migration
    assert "/opt/co-story/releases/%i/.venv/bin/python -m app.commands.migrate" in migration
    assert "User=co-story" in candidate
    assert "EnvironmentFile=/etc/co-story/database.env" in candidate
    assert "--host 127.0.0.1" in candidate
    assert "--port 8001" in candidate
    assert "--workers 1" in candidate


def test_activation_migrates_and_checks_candidate_before_atomic_current_switch() -> None:
    activate = _read(ACTIVATE_SCRIPT)

    migrate_at = activate.index("co-story-migrate@")
    candidate_at = activate.index('candidate_unit="co-story-candidate@', migrate_at)
    ready_before_switch = activate.index("/api/v1/ready", candidate_at)
    switch_at = activate.index("mv -Tf", ready_before_switch)
    restart_at = activate.index("systemctl restart co-story.service", switch_at)
    ready_after_restart = activate.rindex("/api/v1/ready")
    assert migrate_at < candidate_at < ready_before_switch < switch_at < restart_at < ready_after_restart
    assert "current.restore" in activate
    assert "ln -s" in activate
    assert "current.previous" in activate
    assert "set -x" not in activate
    assert "DATABASE_URL" not in activate
    assert 'if [ -L "$ROOT/current" ]' in activate
    assert "remove unverified first deployment" in activate
    assert activate.count('--header "Host: $health_host"') == 2


def test_rollback_validates_candidate_without_migrating_or_downgrading_schema() -> None:
    rollback = _read(ROLLBACK_SCRIPT)
    lowered = rollback.lower()

    assert "co-story-candidate@" in rollback
    assert "/api/v1/ready" in rollback
    assert "mv -Tf" in rollback
    move_lines = [line.strip() for line in rollback.splitlines() if line.strip().startswith("mv ")]
    assert move_lines
    assert all("mv -Tf" in line for line in move_lines)
    assert "current.restore" in rollback
    assert "co-story-migrate@" not in rollback
    assert "migrate" not in lowered
    assert "psql" not in lowered
    assert "down" not in lowered
    assert "database_url" not in lowered


def test_activation_and_rollback_bound_transient_readiness_retries() -> None:
    for path in (ACTIVATE_SCRIPT, ROLLBACK_SCRIPT):
        script = _read(path)

        assert "wait_for_readiness()" in script
        assert "readiness_attempts=30" in script
        assert "sleep 1" in script
        assert "readiness check failed" in script
