from pathlib import Path


ROOT = Path(__file__).parents[2]
NGINX_CONFIG = ROOT / "ops/nginx/co-story.conf"
SYSTEMD_UNIT = ROOT / "ops/systemd/co-story.service"
RUNTIME_ENV_EXAMPLE = ROOT / "ops/runtime/co-story.env.example"


def _read(path: Path) -> str:
    assert path.is_file(), f"runtime asset 尚未建立：{path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def test_nginx_only_exposes_tls_and_proxies_to_loopback_single_process() -> None:
    config = _read(NGINX_CONFIG)

    assert "listen 80;" in config
    assert "return 301 https://$host$request_uri;" in config
    assert "listen 443 ssl;" in config
    assert "proxy_pass http://127.0.0.1:8000;" in config
    assert "0.0.0.0:8000" not in config
    assert "ssl_certificate" not in config
    assert "/etc/nginx/co-story-tls.conf" in config


def test_systemd_runs_one_non_root_uvicorn_process_with_external_environment() -> None:
    unit = _read(SYSTEMD_UNIT)

    assert "User=co-story" in unit
    assert "Group=co-story" in unit
    assert "EnvironmentFile=/etc/co-story/runtime.env" in unit
    assert "ExecStart=/opt/co-story/current/.venv/bin/uvicorn" in unit
    assert "/opt/co-story/venv" not in unit
    assert "--host 127.0.0.1" in unit
    assert "--port 8000" in unit
    assert "--workers 1" in unit
    assert "NoNewPrivileges=true" in unit
    assert "PrivateTmp=true" in unit
    assert "ProtectSystem=strict" in unit
    assert "DATABASE_URL=" not in unit
    assert "CO_STORY_" not in unit


def test_runtime_environment_example_declares_names_without_secrets() -> None:
    environment = _read(RUNTIME_ENV_EXAMPLE)

    assert "CO_STORY_ENV=production" in environment
    assert "DATABASE_URL=" in environment
    assert "CO_STORY_COOKIE_SECURE=true" in environment
    assert "CO_STORY_ALLOWED_HOSTS=" in environment
    assert "CO_STORY_ALLOWED_ORIGINS=" in environment
    assert "password" not in environment.lower()
    assert "postgresql://" not in environment.lower()
