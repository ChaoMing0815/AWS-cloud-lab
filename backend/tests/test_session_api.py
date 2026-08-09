import json

from fastapi.testclient import TestClient

from app.main import create_app


def create_room(client: TestClient, key: str = "session-room") -> dict:
    response = client.post(
        "/api/v1/rooms",
        json={"nickname": "房主"},
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 201
    return response.json()


def test_anonymous_session_summary_does_not_fall_back_to_demo() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/session/current")

    assert response.status_code == 200
    assert response.json() == {
        "authenticated": False,
        "principalType": "anonymous",
        "isHost": False,
        "room": None,
        "continueRoute": None,
    }


def test_host_player_session_summary_routes_draft_to_setup_without_secrets() -> None:
    with TestClient(create_app()) as client:
        room = create_room(client)
        response = client.get("/api/v1/session/current")

    payload = response.json()
    assert response.status_code == 200
    assert payload == {
        "authenticated": True,
        "principalType": "player",
        "isHost": True,
        "room": {
            "id": room["id"],
            "roomCode": room["roomCode"],
            "status": "DRAFT",
        },
        "continueRoute": "/host/setup",
    }
    serialized = json.dumps(payload).lower()
    assert "token" not in serialized
    assert "csrf" not in serialized
    assert "hash" not in serialized
    assert "action" not in serialized


def test_session_summary_maps_canonical_room_states_to_routes() -> None:
    app = create_app()
    with TestClient(app) as client:
        room = create_room(client, "session-route-room")
        service = app.state.room_service
        stored = service.repository.get(room["id"])
        assert stored is not None

        cases = {
            "LOBBY": f"/room/{room['roomCode']}/lobby",
            "COLLECTING_ACTIONS": f"/room/{room['roomCode']}/play",
            "AWAITING_SPARK": f"/room/{room['roomCode']}/play",
            "COMPLETION_AVAILABLE": f"/room/{room['roomCode']}/play",
            "COMPLETED": f"/room/{room['roomCode']}/ending",
        }
        for status, expected_route in cases.items():
            stored.status = status
            service.repository.save(stored)
            response = client.get("/api/v1/session/current")
            assert response.status_code == 200
            assert response.json()["continueRoute"] == expected_route


def test_stale_or_invalid_session_pointer_is_rejected() -> None:
    app = create_app()
    with TestClient(app) as owner:
        room = create_room(owner, "invalid-session-room")

    with TestClient(app) as outsider:
        outsider.cookies.set("co_story_local_room", room["id"])
        outsider.cookies.set("co_story_player", "invalid-player-token")
        response = outsider.get("/api/v1/session/current")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"
