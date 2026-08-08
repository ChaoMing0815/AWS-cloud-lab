from fastapi.testclient import TestClient

from app.main import create_app


def headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


def new_room(client: TestClient, key: str = "create-room-0001") -> dict:
    response = client.post("/api/v1/rooms", headers=headers(key))
    assert response.status_code == 201
    return response.json()


def test_create_room_and_restore_it_from_http_only_cookie() -> None:
    with TestClient(create_app()) as client:
        room = new_room(client)
        restored = client.get("/api/v1/rooms/current")

    assert restored.status_code == 200
    assert restored.json()["id"] == room["id"]
    assert restored.json()["players"] == []
    assert "co_story_local_room=" in restored.request.headers.get("cookie", "")
    assert room["session"]["principalType"] == "host"
    assert client.cookies.get("co_story_host")


def test_join_room_and_reject_duplicate_nickname() -> None:
    with TestClient(create_app()) as client:
        room = new_room(client)
        joined = client.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "小明", "role": "細心的企劃", "room_version": room["version"]},
            headers=headers("join-room-0001"),
        )
        duplicate = client.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "小明", "role": "工程師", "room_version": joined.json()["version"]},
            headers=headers("join-room-0002"),
        )

    assert joined.status_code == 201
    assert joined.json()["players"][0]["name"] == "小明"
    assert joined.json()["session"]["principalType"] == "player"
    assert joined.json()["session"]["playerId"] == joined.json()["players"][0]["id"]
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "NICKNAME_TAKEN"


def test_version_conflict_returns_structured_error() -> None:
    with TestClient(create_app()) as client:
        room = new_room(client)
        response = client.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "小明", "role": "企劃", "room_version": room["version"] + 99},
            headers=headers("join-room-conflict"),
        )

    assert response.status_code == 409
    assert response.json() == {
        "error": {"code": "VERSION_CONFLICT", "message": "房間狀態已更新，請重新載入。"}
    }


def test_missing_idempotency_key_is_rejected() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/v1/rooms")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_join_replay_does_not_create_second_player() -> None:
    with TestClient(create_app()) as client:
        room = new_room(client)
        payload = {"nickname": "小明", "role": "企劃", "room_version": room["version"]}
        first = client.post(
            f"/api/v1/rooms/{room['id']}/players",
            json=payload,
            headers=headers("join-replay-0001"),
        )
        replay = client.post(
            f"/api/v1/rooms/{room['id']}/players",
            json=payload,
            headers=headers("join-replay-0001"),
        )

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json()["players"] == first.json()["players"]
    assert replay.json()["version"] == first.json()["version"]


def test_idempotency_key_cannot_be_reused_with_different_payload() -> None:
    with TestClient(create_app()) as client:
        room = new_room(client)
        client.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "小明", "role": "企劃", "room_version": room["version"]},
            headers=headers("join-reused-0001"),
        )
        reused = client.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "小華", "role": "工程師", "room_version": room["version"]},
            headers=headers("join-reused-0001"),
        )

    assert reused.status_code == 422
    assert reused.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_action_requires_player_session_and_csrf() -> None:
    app = create_app()
    with TestClient(app) as player_client, TestClient(app) as attacker:
        room = new_room(player_client)
        joined = player_client.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "小明", "role": "企劃", "room_version": room["version"]},
            headers=headers("join-for-action"),
        ).json()
        action_url = f"/api/v1/rooms/{room['id']}/rounds/{room['round']}/action"
        payload = {"text": "我先確認門口狀況。", "room_version": joined["version"]}

        no_session = attacker.put(
            action_url,
            json=payload,
            headers={**headers("action-no-session"), "X-CSRF-Token": joined["session"]["csrfToken"]},
        )
        no_csrf = player_client.put(action_url, json=payload, headers=headers("action-no-csrf"))
        accepted = player_client.put(
            action_url,
            json=payload,
            headers={**headers("action-ok-0001"), "X-CSRF-Token": joined["session"]["csrfToken"]},
        )

    assert no_session.status_code == 401
    assert no_session.json()["error"]["code"] == "PLAYER_SESSION_REQUIRED"
    assert no_csrf.status_code == 403
    assert no_csrf.json()["error"]["code"] == "CSRF_FAILED"
    assert accepted.status_code == 200
    assert accepted.json()["players"][0]["hasSubmitted"] is True
    assert accepted.json()["players"][0]["action"] == "我先確認門口狀況。"


def test_unrevealed_action_text_is_hidden_from_other_player() -> None:
    app = create_app()
    with TestClient(app) as host, TestClient(app) as first_player, TestClient(app) as second_player:
        room = new_room(host)
        first = first_player.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "甲", "role": "企劃", "room_version": room["version"]},
            headers=headers("join-player-one"),
        ).json()
        second = second_player.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "乙", "role": "工程師", "room_version": first["version"]},
            headers=headers("join-player-two"),
        ).json()
        submitted = first_player.put(
            f"/api/v1/rooms/{room['id']}/rounds/{room['round']}/action",
            json={"text": "這是尚未揭露的行動。", "room_version": second["version"]},
            headers={**headers("hidden-action-1"), "X-CSRF-Token": first["session"]["csrfToken"]},
        )
        observed = second_player.get("/api/v1/rooms/current")

    assert submitted.status_code == 200
    first_in_other_view = next(player for player in observed.json()["players"] if player["name"] == "甲")
    assert first_in_other_view["hasSubmitted"] is True
    assert first_in_other_view["action"] == ""
    assert "這是尚未揭露的行動。" not in observed.text
