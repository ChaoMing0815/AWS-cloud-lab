from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class MutableClock:
    def __init__(self, now: datetime) -> None:
        self.now_value = now

    def now(self) -> datetime:
        return self.now_value

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
WORLD = {
    "story_title": "午夜便利商店大作戰",
    "premise": "午夜便利商店的夜班盤點資料突然消失，店長將在天亮前抵達逐一檢查所有紀錄，三位夥伴必須在有限時間內找回備份並完成核對。",
    "objective": "找回盤點資料並完成正確報表。",
    "opening_scene": "凌晨兩點，收銀機突然重開機，唯一的盤點檔案也從共用資料夾消失。",
    "core_obstacle": "備份硬碟被鎖在倉庫，而密碼只有前任店員知道。",
    "tone": "slice_of_life",
    "custom_tone": None,
    "max_rounds": 6,
}
CHARACTER = {
    "name": "夜班調查員",
    "background": "熟悉門市每一個角落與所有交班紀錄。",
    "trait": "遇事冷靜",
    "weakness": "太容易懷疑自己",
    "courage": 2,
    "insight": 1,
    "bond": 0,
}

def _app_and_clock():
    clock = MutableClock(NOW)
    return create_app(clock=clock), clock

def _create_room(client: TestClient, key: str = "expiry-create-room") -> dict:
    response = client.post(
        "/api/v1/rooms",
        json={"nickname": "房主"},
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 201
    return response.json()

def _stored_room(app, room_id: str):
    room = app.state.room_service.repository.get(room_id)
    assert room is not None
    return room

def _save_expiries(
    app,
    room_id: str,
    *,
    room_expiry: datetime | None,
    host_expiry: datetime | None,
    player_expiry: datetime | None,
) -> None:
    room = _stored_room(app, room_id)
    room.expires_at = room_expiry
    room.host_session_expires_at = host_expiry
    room.players[0].session_expires_at = player_expiry
    app.state.room_service.repository.save(room)

def _future() -> datetime:
    return NOW + timedelta(days=1)


def _expired() -> datetime:
    return NOW - timedelta(microseconds=1)

def _host_world_request(client: TestClient, room: dict, key: str, *, csrf: str | None = None):
    return client.put(
        f"/api/v1/rooms/{room['id']}/world",
        json={**WORLD, "room_version": room["version"]},
        headers={
            "Idempotency-Key": key,
            "X-CSRF-Token": csrf if csrf is not None else room["session"]["hostCsrfToken"],
        },
    )

def _player_character_request(
    client: TestClient,
    room: dict,
    key: str,
    *,
    csrf: str | None = None,
    version: int | None = None,
):
    return client.put(
        f"/api/v1/rooms/{room['id']}/character",
        json={**CHARACTER, "room_version": room["version"] if version is None else version},
        headers={
            "Idempotency-Key": key,
            "X-CSRF-Token": csrf if csrf is not None else room["session"]["csrfToken"],
        },
    )

@pytest.mark.parametrize(
    ("room_expiry", "expected_status"),
    [
        (None, 401),
        (_expired(), 401),
        (NOW, 401),
        (_future(), 200),
    ],
    ids=("missing", "after", "at-boundary", "before"),
)
def test_current_reads_enforce_room_expiry_boundary(
    room_expiry: datetime | None, expected_status: int
) -> None:
    app, _ = _app_and_clock()
    with TestClient(app) as client:
        room = _create_room(client)
        _save_expiries(
            app,
            room["id"],
            room_expiry=room_expiry,
            host_expiry=_future(),
            player_expiry=_future(),
        )

        summary = client.get("/api/v1/session/current")
        polling = client.get("/api/v1/rooms/current")

    assert summary.status_code == expected_status
    assert polling.status_code == expected_status
    if expected_status == 401:
        assert summary.json()["error"]["code"] == "SESSION_NOT_FOUND"
        assert polling.json()["error"]["code"] == "SESSION_NOT_FOUND"

@pytest.mark.parametrize(
    ("host_expiry", "expected_status"),
    [
        (None, 401),
        (_expired(), 401),
        (NOW, 401),
        (_future(), 200),
    ],
    ids=("missing", "after", "at-boundary", "before"),
)
def test_host_mutation_enforces_host_session_expiry_boundary(
    host_expiry: datetime | None, expected_status: int
) -> None:
    app, _ = _app_and_clock()
    with TestClient(app) as client:
        room = _create_room(client)
        _save_expiries(
            app,
            room["id"],
            room_expiry=_future(),
            host_expiry=host_expiry,
            player_expiry=_future(),
        )
        response = _host_world_request(client, room, "host-expiry-boundary")

    assert response.status_code == expected_status
    if expected_status == 401:
        assert response.json()["error"]["code"] == "HOST_SESSION_REQUIRED"

@pytest.mark.parametrize(
    ("player_expiry", "expected_status"),
    [
        (None, 401),
        (_expired(), 401),
        (NOW, 401),
        (_future(), 200),
    ],
    ids=("missing", "after", "at-boundary", "before"),
)
def test_player_mutation_enforces_player_session_expiry_boundary(
    player_expiry: datetime | None, expected_status: int
) -> None:
    app, _ = _app_and_clock()
    with TestClient(app) as client:
        room = _create_room(client)
        stored = _stored_room(app, room["id"])
        stored.status = "LOBBY"
        app.state.room_service.repository.save(stored)
        _save_expiries(
            app,
            room["id"],
            room_expiry=_future(),
            host_expiry=_future(),
            player_expiry=player_expiry,
        )
        response = _player_character_request(client, room, "player-expiry-boundary")

    assert response.status_code == expected_status
    if expected_status == 401:
        assert response.json()["error"]["code"] == "PLAYER_SESSION_REQUIRED"

def test_host_and_player_sessions_expire_independently() -> None:
    app, _ = _app_and_clock()
    with TestClient(app) as client:
        room = _create_room(client)
        stored = _stored_room(app, room["id"])
        stored.status = "LOBBY"
        app.state.room_service.repository.save(stored)
        _save_expiries(
            app,
            room["id"],
            room_expiry=_future(),
            host_expiry=NOW,
            player_expiry=_future(),
        )
        host_rejected = _host_world_request(client, room, "expired-host-only")
        player_allowed = _player_character_request(client, room, "valid-player-only")

    assert host_rejected.status_code == 401
    assert host_rejected.json()["error"]["code"] == "HOST_SESSION_REQUIRED"
    assert player_allowed.status_code == 200


@pytest.mark.parametrize(
    ("host_expiry", "player_expiry", "principal_type", "is_host"),
    [
        (NOW, _future(), "player", False),
        (_future(), NOW, "host", True),
    ],
    ids=("expired-host-keeps-player", "expired-player-keeps-host"),
)
def test_current_session_independently_downgrades_expired_principal(
    host_expiry: datetime,
    player_expiry: datetime,
    principal_type: str,
    is_host: bool,
) -> None:
    app, _ = _app_and_clock()
    with TestClient(app) as client:
        room = _create_room(client)
        _save_expiries(
            app,
            room["id"],
            room_expiry=_future(),
            host_expiry=host_expiry,
            player_expiry=player_expiry,
        )
        response = client.get("/api/v1/session/current")

    assert response.status_code == 200
    assert response.json()["principalType"] == principal_type
    assert response.json()["isHost"] is is_host

def test_expired_session_wins_over_csrf_and_version_errors() -> None:
    app, _ = _app_and_clock()
    with TestClient(app) as client:
        room = _create_room(client)
        stored = _stored_room(app, room["id"])
        stored.status = "LOBBY"
        app.state.room_service.repository.save(stored)
        _save_expiries(
            app,
            room["id"],
            room_expiry=_future(),
            host_expiry=NOW,
            player_expiry=NOW,
        )
        host_response = _host_world_request(
            client,
            room,
            "expired-host-before-csrf-version",
            csrf="wrong-csrf",
        )
        player_response = _player_character_request(
            client,
            room,
            "expired-player-before-csrf-version",
            csrf="wrong-csrf",
            version=room["version"] + 1,
        )

    assert host_response.status_code == 401
    assert host_response.json()["error"]["code"] == "HOST_SESSION_REQUIRED"
    assert player_response.status_code == 401
    assert player_response.json()["error"]["code"] == "PLAYER_SESSION_REQUIRED"

def test_expired_replay_is_rejected_before_idempotency_and_does_not_refresh() -> None:
    app, clock = _app_and_clock()
    with TestClient(app) as client:
        room = _create_room(client)
        first = _host_world_request(client, room, "replay-after-expiry")
        assert first.status_code == 200
        stored = _stored_room(app, room["id"])
        stored.host_session_expires_at = clock.now()
        app.state.room_service.repository.save(stored)

        replay = _host_world_request(client, room, "replay-after-expiry")
        persisted = _stored_room(app, room["id"])

    assert replay.status_code == 401
    assert replay.json()["error"]["code"] == "HOST_SESSION_REQUIRED"
    assert persisted.host_session_expires_at == NOW

def test_current_reads_and_polling_never_extend_expiry() -> None:
    app, _ = _app_and_clock()
    with TestClient(app) as client:
        room = _create_room(client)
        original = (_future(), _future(), _future())
        _save_expiries(
            app,
            room["id"],
            room_expiry=original[0],
            host_expiry=original[1],
            player_expiry=original[2],
        )

        summary = client.get("/api/v1/session/current")
        polling = client.get("/api/v1/rooms/current")
        persisted = _stored_room(app, room["id"])

    assert summary.status_code == 200
    assert polling.status_code == 200
    assert (
        persisted.expires_at,
        persisted.host_session_expires_at,
        persisted.players[0].session_expires_at,
    ) == original

@pytest.mark.parametrize(
    ("room_expiry", "expected_status"),
    [(_future(), 200), (NOW, 401)],
    ids=("inside-retention", "at-retention-boundary"),
)
def test_completed_room_is_readable_only_inside_retention_period(
    room_expiry: datetime, expected_status: int
) -> None:
    app, _ = _app_and_clock()
    with TestClient(app) as client:
        room = _create_room(client)
        stored = _stored_room(app, room["id"])
        stored.status = "COMPLETED"
        app.state.room_service.repository.save(stored)
        _save_expiries(
            app,
            room["id"],
            room_expiry=room_expiry,
            host_expiry=_future(),
            player_expiry=_future(),
        )
        response = client.get("/api/v1/rooms/current")

    assert response.status_code == expected_status
    if expected_status == 401:
        assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"
