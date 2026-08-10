import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.adapters.postgres_migrations import apply_migrations
from app.api.routes import HOST_SESSION_COOKIE, LOCAL_ROOM_COOKIE, PLAYER_SESSION_COOKIE
from app.main import create_app


@pytest.mark.skipif(
    "CO_STORY_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定專題 PostgreSQL 測試資料庫",
)
def test_room_and_session_survive_application_restart(monkeypatch) -> None:
    dsn = os.environ["CO_STORY_TEST_DATABASE_URL"]
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM rooms")
    monkeypatch.setenv("DATABASE_URL", dsn)

    with TestClient(create_app()) as first_process:
        created_response = first_process.post(
            "/api/v1/rooms",
            json={"nickname": "重新連線的房主"},
            headers={"Idempotency-Key": "restart-create-room"},
        )
        assert created_response.status_code == 201
        created = created_response.json()
        session_cookies = {
            name: created_response.cookies[name]
            for name in (LOCAL_ROOM_COOKIE, HOST_SESSION_COOKIE, PLAYER_SESSION_COOKIE)
        }

    with TestClient(create_app()) as restarted_process:
        restored_response = restarted_process.get(
            "/api/v1/rooms/current",
            cookies=session_cookies,
        )

    assert restored_response.status_code == 200
    restored = restored_response.json()
    assert restored["id"] == created["id"]
    assert restored["roomCode"] == created["roomCode"]
    assert restored["session"]["isHost"] is True
    assert restored["session"]["currentPlayerId"] == created["session"]["currentPlayerId"]
