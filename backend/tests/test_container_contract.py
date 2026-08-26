import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[2]
DOCKERFILE = ROOT / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
HEALTHCHECK = ROOT / "ops/container/healthcheck.py"
SYSTEMD_UNIT = ROOT / "ops/systemd/co-story-container.service"


def _read(path: Path) -> str:
    assert path.is_file(), f"container asset 尚未建立：{path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def test_image_is_non_root_secret_free_and_keeps_the_runtime_contract() -> None:
    dockerfile = _read(DOCKERFILE)
    dockerignore = _read(DOCKERIGNORE)

    assert "FROM python:3.13" in dockerfile
    assert "pip install --no-cache-dir" in dockerfile
    assert "backend/requirements-prod.txt" in dockerfile
    assert "COPY backend" in dockerfile
    assert "COPY web" in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert "EXPOSE 8000" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert '"127.0.0.1"' in dockerfile
    assert '"8000"' in dockerfile
    assert '\"--workers\", \"1\"' in dockerfile
    assert "DATABASE_URL=" not in dockerfile
    assert "CO_STORY_BEDROCK_GUARDRAIL_ID=" not in dockerfile
    assert ".env" in dockerignore
    assert ".git" in dockerignore
    assert "docs/evidence" in dockerignore


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def _healthcheck_module():
    assert HEALTHCHECK.is_file(), "container healthcheck 尚未建立"
    spec = importlib.util.spec_from_file_location("container_healthcheck", HEALTHCHECK)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_container_healthcheck_requires_both_live_and_ready_without_leaking_body(capsys) -> None:
    module = _healthcheck_module()
    requested: list[str] = []

    def healthy(request, timeout):
        assert timeout == 5
        requested.append(request.full_url)
        return _Response()

    assert module.main(open_url=healthy, host="localhost", port=8000) == 0
    assert requested == [
        "http://127.0.0.1:8000/api/v1/live",
        "http://127.0.0.1:8000/api/v1/ready",
    ]

    def unavailable(request, timeout):
        if request.full_url.endswith("/ready"):
            raise OSError("sensitive-response-must-not-be-logged")
        return _Response()

    assert module.main(open_url=unavailable, host="localhost", port=8000) == 1
    captured = capsys.readouterr()
    assert "sensitive-response-must-not-be-logged" not in captured.out
    assert "sensitive-response-must-not-be-logged" not in captured.err


def test_container_systemd_keeps_nginx_edge_and_external_runtime_injection() -> None:
    unit = _read(SYSTEMD_UNIT)

    assert "User=root" in unit
    assert "EnvironmentFile=/etc/co-story/container-release.env" in unit
    assert "--network host" in unit
    assert "--env-file /etc/co-story/runtime.env" in unit
    assert "--env-file /etc/co-story/database.env" in unit
    assert "/var/log/co-story:/var/log/co-story" in unit
    assert "--host 127.0.0.1" in unit
    assert "--port 8000" in unit
    assert "--workers 1" in unit
    assert "DATABASE_URL=" not in unit
    assert "--privileged" not in unit
    assert "--network bridge" not in unit
