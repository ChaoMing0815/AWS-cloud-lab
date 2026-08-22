import json
import logging

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

        assert log_path.is_file(), "安全 application JSONL file 尚未建立"
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
    finally:
        monkeypatch.delenv("CO_STORY_APPLICATION_LOG_PATH", raising=False)
        create_app()
