import json
import logging
import stat

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def test_safe_application_file_collects_only_allowlisted_json_events(
    tmp_path,
    monkeypatch,
) -> None:
    log_path = tmp_path / "application.jsonl"
    monkeypatch.setenv("CO_STORY_APPLICATION_LOG_PATH", str(log_path))

    try:
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/api/v1/live?token=never-log-this")

        logging.getLogger("co_story.storyteller").warning(
            json.dumps(
                {
                    "operation": "generate_world",
                    "failure_code": "TIMEOUT",
                },
                separators=(",", ":"),
            )
        )
        logging.getLogger("uvicorn.access").warning(
            'GET /api/v1/live?token=raw-access-secret HTTP/1.1 200'
        )
        logging.getLogger("co_story.request").warning(
            json.dumps(
                {
                    "request_id": "forged",
                    "secret": "forged-safe-logger-secret",
                }
            )
        )

        assert log_path.is_file(), "安全 application JSONL file 尚未建立"
        assert stat.S_IMODE(log_path.stat().st_mode) == 0o640
        events = [
            json.loads(line)
            for line in log_path.read_text(encoding="utf-8").splitlines()
        ]
        assert any(
            event.get("path") == "/api/v1/live" and event.get("status") == 200
            for event in events
        )
        assert {
            "operation": "generate_world",
            "failure_code": "TIMEOUT",
        } in events

        rendered = log_path.read_text(encoding="utf-8")
        assert "never-log-this" not in rendered
        assert "raw-access-secret" not in rendered
        assert "forged-safe-logger-secret" not in rendered
    finally:
        monkeypatch.delenv("CO_STORY_APPLICATION_LOG_PATH", raising=False)
        create_app()


def test_safe_application_file_rotates_and_refuses_symlink_target(
    tmp_path,
    monkeypatch,
) -> None:
    log_path = tmp_path / "application.jsonl"
    monkeypatch.setenv("CO_STORY_APPLICATION_LOG_PATH", str(log_path))

    try:
        create_app()
        logger = logging.getLogger("co_story.request")
        long_path = "/api/v1/" + ("x" * 2048)
        previous_propagate = logger.propagate
        logger.propagate = False
        try:
            for index in range(600):
                logger.info(
                    json.dumps(
                        {
                            "request_id": f"rotation-{index}",
                            "method": "GET",
                            "path": long_path,
                            "status": 200,
                            "latency_ms": 1,
                        },
                        separators=(",", ":"),
                    )
                )
        finally:
            logger.propagate = previous_propagate

        rotated_files = sorted(tmp_path.glob("application.jsonl*"))
        assert any(path.name == "application.jsonl.1" for path in rotated_files)
        assert len(rotated_files) <= 3
        assert all(path.stat().st_size <= 1024 * 1024 for path in rotated_files)
        assert all(stat.S_IMODE(path.stat().st_mode) == 0o640 for path in rotated_files)
    finally:
        monkeypatch.delenv("CO_STORY_APPLICATION_LOG_PATH", raising=False)
        create_app()

    real_file = tmp_path / "real.log"
    real_file.write_text("do-not-follow", encoding="utf-8")
    symlink_path = tmp_path / "symlinked-application.jsonl"
    symlink_path.symlink_to(real_file)
    monkeypatch.setenv("CO_STORY_APPLICATION_LOG_PATH", str(symlink_path))
    try:
        with pytest.raises(RuntimeError, match="CO_STORY_APPLICATION_LOG_PATH"):
            create_app()
        assert real_file.read_text(encoding="utf-8") == "do-not-follow"
    finally:
        monkeypatch.delenv("CO_STORY_APPLICATION_LOG_PATH", raising=False)
        create_app()
