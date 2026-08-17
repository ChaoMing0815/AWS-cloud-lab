import json

from fastapi.testclient import TestClient

from app.main import create_app


def _request_events(caplog) -> list[dict]:
    return [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "co_story.request"
    ]


def test_api_request_log_is_structured_allowlist_with_generated_request_id(caplog) -> None:
    app = create_app()
    caplog.set_level("INFO", logger="co_story.request")

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/live?token=never-log-this",
            headers={
                "Authorization": "Bearer never-log-this",
                "Cookie": "co_story_host=never-log-this",
                "X-Request-ID": "attacker-controlled",
            },
        )

    events = _request_events(caplog)
    assert response.status_code == 200
    assert response.headers["x-request-id"] != "attacker-controlled"
    assert len(events) == 1
    assert set(events[0]) == {"request_id", "method", "path", "status", "latency_ms"}
    assert events[0]["request_id"] == response.headers["x-request-id"]
    assert events[0]["method"] == "GET"
    assert events[0]["path"] == "/api/v1/live"
    assert events[0]["status"] == 200
    assert isinstance(events[0]["latency_ms"], int)

    rendered = caplog.text
    assert "never-log-this" not in rendered
    assert "attacker-controlled" not in rendered


def test_rejected_request_is_logged_without_origin_or_request_body(caplog, monkeypatch) -> None:
    monkeypatch.setenv("CO_STORY_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://app:secret@db.example.test/co_story?sslmode=verify-full&sslrootcert=/run/certs/rds-ca.pem",
    )
    monkeypatch.setenv("CO_STORY_COOKIE_SECURE", "true")
    monkeypatch.setenv("CO_STORY_ALLOWED_HOSTS", "app.example.test")
    monkeypatch.setenv("CO_STORY_ALLOWED_ORIGINS", "https://app.example.test")
    app = create_app(room_repository=object(), storyteller=object())
    caplog.set_level("INFO", logger="co_story.request")

    with TestClient(app, base_url="https://app.example.test") as client:
        response = client.post(
            "/api/v1/rooms",
            json={"nickname": "秘密玩家名稱"},
            headers={"Origin": "https://attacker.example.test"},
        )

    event = _request_events(caplog)[0]
    assert response.status_code == 403
    assert event["status"] == 403
    assert "秘密玩家名稱" not in caplog.text
    assert "attacker.example.test" not in caplog.text
