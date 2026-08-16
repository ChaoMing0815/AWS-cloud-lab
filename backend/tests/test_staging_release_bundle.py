import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[2]
BUILD = ROOT / "ops/release/build_bundle.sh"
INSTALL = ROOT / "ops/release/install_staging.sh"
STAGING_NGINX = ROOT / "ops/nginx/co-story-staging.conf"
STAGING_NGINX_UNIT = ROOT / "ops/systemd/co-story-nginx-staging.service"


def _read(path: Path) -> str:
    assert path.is_file(), f"staging release asset 尚未建立：{path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def test_bundle_builder_archives_only_committed_head_with_checksum_and_installer() -> None:
    script = _read(BUILD)

    assert "git status --porcelain" in script
    assert "git archive" in script
    assert "HEAD backend web ops" in script
    assert "gzip -n" in script
    assert "shasum -a 256" in script
    assert "co-story.tar.gz.sha256" in script
    assert "install_staging.sh" in script
    assert "set -x" not in script
    assert "DATABASE_URL" not in script


def test_staging_installer_verifies_artifact_before_extracting_or_installing() -> None:
    script = _read(INSTALL)

    checksum_at = script.index("sha256sum -c")
    extract_at = script.index("tar -xzf")
    package_at = script.index("dnf install")
    assert checksum_at < extract_at < package_at
    assert "python3.13" in script
    assert "python3.13-pip" in script
    assert "nginx" in script
    assert "--no-deps" in script
    assert "requirements-prod.txt" in script


def test_staging_installer_keeps_secret_values_out_of_commands_and_files() -> None:
    script = _read(INSTALL)

    assert "bootstrap_database.py" in script
    assert "CO_STORY_MASTER_SECRET_ARN" in script
    assert "CO_STORY_APP_DB_SECRET_ARN" in script
    assert "CO_STORY_DB_ENDPOINT" in script
    assert "DATABASE_URL=" not in script
    assert "get-secret-value" not in script
    assert "aws secretsmanager" not in script
    assert "set -x" not in script
    assert "password" not in script.lower()


def test_staging_installer_uses_non_root_service_and_internal_only_proxy() -> None:
    script = _read(INSTALL)
    nginx = _read(STAGING_NGINX)
    nginx_unit = _read(STAGING_NGINX_UNIT)

    assert "useradd --system" in script
    assert "co-story" in script
    assert "co-story.service" in script
    assert 'systemctl start "co-story-migrate@' not in script
    assert "activate.sh" in script
    assert "systemctl enable" in script
    assert "systemctl disable --now nginx.service" in script
    assert "co-story-nginx-staging.service" in script
    assert "previous_target" in script
    assert "install-restore" in script
    assert "listen 127.0.0.1:8080;" in nginx
    assert "proxy_pass http://127.0.0.1:8000;" in nginx
    assert "listen 80" not in nginx
    assert "listen 443" not in nginx
    assert "0.0.0.0" not in nginx
    assert "access_log off;" in nginx
    assert "/dev/stdout" not in nginx
    assert "-e stderr" in nginx_unit
    assert "ProtectSystem=strict" in nginx_unit


def test_staging_installer_bounds_proxy_readiness_retries() -> None:
    script = _read(INSTALL)

    assert "wait_for_readiness()" in script
    assert "readiness_attempts=30" in script
    assert "sleep 1" in script
    assert "readiness check failed" in script


def test_staging_installer_removes_only_an_unresolvable_current_symlink() -> None:
    script = _read(INSTALL)

    assert 'if [ -L "$root/current" ] && [ -z "$active_target" ]; then' in script
    assert 'rm -f "$root/current"' in script
    assert 'systemctl stop co-story.service || true' in script


def test_release_shell_assets_have_valid_bash_syntax() -> None:
    for script in (BUILD, INSTALL):
        result = subprocess.run(
            ["bash", "-n", script],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
