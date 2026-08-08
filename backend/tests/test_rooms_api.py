from fastapi.testclient import TestClient

from app.main import create_app

WORLD_PAYLOAD = {
    "story_title": "午夜便利商店大作戰",
    "premise": "三位夜班夥伴發現年度盤點資料離奇消失，店長將在天亮前抵達並檢查所有紀錄；若無法及時找回，全體都得留下重新盤點整間門市。",
    "objective": "在店長抵達前找回盤點資料並完成正確報表。",
    "opening_scene": "凌晨兩點，收銀機突然重開機，唯一的盤點檔案也從共用資料夾消失了。",
    "core_obstacle": "備份硬碟被鎖在倉庫，而唯一知道密碼的前任店員已經離職。",
    "tone": "slice_of_life",
    "custom_tone": None,
    "max_rounds": 6,
}

CHARACTER_PAYLOAD = {
    "name": "夜班調查員",
    "background": "熟悉門市每一個角落與所有交班紀錄。",
    "trait": "遇事冷靜",
    "weakness": "太容易懷疑自己",
    "courage": 2,
    "insight": 1,
    "bond": 0,
}


def headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


def new_room(client: TestClient, key: str = "create-room-0001") -> dict:
    response = client.post("/api/v1/rooms", headers=headers(key))
    assert response.status_code == 201
    return response.json()


def confirm_world(client: TestClient, room: dict, key: str = "confirm-world-0001") -> dict:
    response = client.put(
        f"/api/v1/rooms/{room['id']}/world",
        json={**WORLD_PAYLOAD, "room_version": room["version"]},
        headers={
            **headers(key),
            "X-CSRF-Token": room["session"]["hostCsrfToken"],
        },
    )
    assert response.status_code == 200
    return response.json()


def new_lobby(client: TestClient, key: str = "create-lobby-0001") -> dict:
    return confirm_world(client, new_room(client, key), f"confirm-{key}")


def update_character(
    client: TestClient,
    room: dict,
    csrf_token: str,
    key: str,
    name: str,
) -> dict:
    response = client.put(
        f"/api/v1/rooms/{room['id']}/character",
        json={**CHARACTER_PAYLOAD, "name": name, "room_version": room["version"]},
        headers={**headers(key), "X-CSRF-Token": csrf_token},
    )
    assert response.status_code == 200
    return response.json()


def test_create_room_and_restore_it_from_http_only_cookie() -> None:
    with TestClient(create_app()) as client:
        room = new_room(client)
        restored = client.get("/api/v1/rooms/current")

    assert restored.status_code == 200
    assert restored.json()["id"] == room["id"]
    assert restored.json()["players"] == []
    assert restored.json()["status"] == "DRAFT"
    assert "co_story_local_room=" in restored.request.headers.get("cookie", "")
    assert room["session"]["principalType"] == "host"
    assert client.cookies.get("co_story_host")


def test_join_room_and_reject_duplicate_nickname() -> None:
    with TestClient(create_app()) as client:
        room = new_lobby(client)
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
        room = new_lobby(client)
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
        room = new_lobby(client)
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
        room = new_lobby(client)
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


def test_world_confirmation_requires_host_session_and_csrf() -> None:
    app = create_app()
    with TestClient(app) as host, TestClient(app) as outsider:
        room = new_room(host)
        payload = {**WORLD_PAYLOAD, "room_version": room["version"]}
        outsider_response = outsider.put(
            f"/api/v1/rooms/{room['id']}/world",
            json=payload,
            headers={
                **headers("world-outsider"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        )
        no_csrf = host.put(
            f"/api/v1/rooms/{room['id']}/world",
            json=payload,
            headers=headers("world-no-csrf"),
        )
        confirmed = host.put(
            f"/api/v1/rooms/{room['id']}/world",
            json=payload,
            headers={
                **headers("world-confirmed"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        )

    assert outsider_response.status_code == 401
    assert outsider_response.json()["error"]["code"] == "HOST_SESSION_REQUIRED"
    assert no_csrf.status_code == 403
    assert no_csrf.json()["error"]["code"] == "CSRF_FAILED"
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "LOBBY"
    assert confirmed.json()["world"]["storyTitle"] == WORLD_PAYLOAD["story_title"]
    assert confirmed.json()["maxRounds"] == 6


def test_only_host_can_start_lobby_with_three_players() -> None:
    app = create_app()
    with (
        TestClient(app) as host,
        TestClient(app) as first_player,
        TestClient(app) as second_player,
        TestClient(app) as third_player,
    ):
        room = new_lobby(host)
        too_early = host.post(
            f"/api/v1/rooms/{room['id']}:start",
            json={"room_version": room["version"]},
            headers={
                **headers("start-too-early"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        )
        first = first_player.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "甲", "role": "企劃", "room_version": room["version"]},
            headers=headers("start-join-one"),
        ).json()
        second = second_player.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "乙", "role": "工程師", "room_version": first["version"]},
            headers=headers("start-join-two"),
        ).json()
        third = third_player.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "丙", "role": "總務", "room_version": second["version"]},
            headers=headers("start-join-three"),
        ).json()
        not_host = first_player.post(
            f"/api/v1/rooms/{room['id']}:start",
            json={"room_version": third["version"]},
            headers={
                **headers("start-not-host"),
                "X-CSRF-Token": first["session"]["csrfToken"],
            },
        )
        incomplete = host.post(
            f"/api/v1/rooms/{room['id']}:start",
            json={"room_version": third["version"]},
            headers={
                **headers("start-incomplete"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        )
        first_ready = update_character(
            first_player, third, first["session"]["csrfToken"], "character-one", "調查員甲"
        )
        second_ready = update_character(
            second_player, first_ready, second["session"]["csrfToken"], "character-two", "調查員乙"
        )
        third_ready = update_character(
            third_player, second_ready, third["session"]["csrfToken"], "character-three", "調查員丙"
        )
        started = host.post(
            f"/api/v1/rooms/{room['id']}:start",
            json={"room_version": third_ready["version"]},
            headers={
                **headers("start-valid"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        )

    assert too_early.status_code == 409
    assert too_early.json()["error"]["code"] == "PLAYER_COUNT_INVALID"
    assert not_host.status_code == 401
    assert not_host.json()["error"]["code"] == "HOST_SESSION_REQUIRED"
    assert incomplete.status_code == 409
    assert incomplete.json()["error"]["code"] == "CHARACTERS_INCOMPLETE"
    assert started.status_code == 200
    assert started.json()["status"] == "COLLECTING_ACTIONS"
    assert started.json()["initialPlayerCount"] == 3
    assert started.json()["entries"][-1]["text"] == WORLD_PAYLOAD["opening_scene"]


def test_player_cannot_join_before_world_confirmation() -> None:
    app = create_app()
    with TestClient(app) as host, TestClient(app) as player:
        room = new_room(host)
        response = player.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "甲", "role": "企劃", "room_version": room["version"]},
            headers=headers("join-draft-room"),
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ROOM_NOT_JOINABLE"


def test_character_requires_player_session_and_valid_three_point_allocation() -> None:
    app = create_app()
    with TestClient(app) as host, TestClient(app) as player, TestClient(app) as attacker:
        room = new_lobby(host)
        joined = player.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "甲", "role": "企劃", "room_version": room["version"]},
            headers=headers("character-join"),
        ).json()
        url = f"/api/v1/rooms/{room['id']}/character"
        payload = {**CHARACTER_PAYLOAD, "room_version": joined["version"]}
        unauthorized = attacker.put(
            url,
            json=payload,
            headers={
                **headers("character-unauthorized"),
                "X-CSRF-Token": joined["session"]["csrfToken"],
            },
        )
        invalid = player.put(
            url,
            json={**payload, "courage": 2, "insight": 2, "bond": 0},
            headers={
                **headers("character-invalid"),
                "X-CSRF-Token": joined["session"]["csrfToken"],
            },
        )
        accepted = player.put(
            url,
            json=payload,
            headers={
                **headers("character-valid"),
                "X-CSRF-Token": joined["session"]["csrfToken"],
            },
        )
        replay = player.put(
            url,
            json=payload,
            headers={
                **headers("character-valid"),
                "X-CSRF-Token": joined["session"]["csrfToken"],
            },
        )

    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"]["code"] == "PLAYER_SESSION_REQUIRED"
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "INVALID_ATTRIBUTE_ALLOCATION"
    assert accepted.status_code == 200
    assert accepted.json()["players"][0]["characterReady"] is True
    assert accepted.json()["players"][0]["character"]["spark"] == 1
    assert replay.json()["version"] == accepted.json()["version"]


def test_action_requires_player_session_and_csrf() -> None:
    app = create_app()
    with (
        TestClient(app) as host,
        TestClient(app) as player_client,
        TestClient(app) as second_player,
        TestClient(app) as third_player,
        TestClient(app) as attacker,
    ):
        room = new_lobby(host)
        joined = player_client.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "小明", "role": "企劃", "room_version": room["version"]},
            headers=headers("join-for-action"),
        ).json()
        second = second_player.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "小華", "role": "工程師", "room_version": joined["version"]},
            headers=headers("join-for-action-two"),
        ).json()
        third = third_player.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "小陳", "role": "總務", "room_version": second["version"]},
            headers=headers("join-for-action-three"),
        ).json()
        first_ready = update_character(
            player_client, third, joined["session"]["csrfToken"], "action-character-one", "調查員一"
        )
        second_ready = update_character(
            second_player,
            first_ready,
            second["session"]["csrfToken"],
            "action-character-two",
            "調查員二",
        )
        third_ready = update_character(
            third_player,
            second_ready,
            third["session"]["csrfToken"],
            "action-character-three",
            "調查員三",
        )
        started = host.post(
            f"/api/v1/rooms/{room['id']}:start",
            json={"room_version": third_ready["version"]},
            headers={
                **headers("start-for-action"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        ).json()
        action_url = f"/api/v1/rooms/{room['id']}/rounds/{room['round']}/action"
        payload = {"text": "我先確認門口狀況。", "room_version": started["version"]}

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
    with (
        TestClient(app) as host,
        TestClient(app) as first_player,
        TestClient(app) as second_player,
        TestClient(app) as third_player,
    ):
        room = new_lobby(host)
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
        third = third_player.post(
            f"/api/v1/rooms/{room['id']}/players",
            json={"nickname": "丙", "role": "總務", "room_version": second["version"]},
            headers=headers("join-player-three"),
        ).json()
        first_ready = update_character(
            first_player, third, first["session"]["csrfToken"], "hidden-character-one", "角色甲"
        )
        second_ready = update_character(
            second_player,
            first_ready,
            second["session"]["csrfToken"],
            "hidden-character-two",
            "角色乙",
        )
        third_ready = update_character(
            third_player,
            second_ready,
            third["session"]["csrfToken"],
            "hidden-character-three",
            "角色丙",
        )
        started = host.post(
            f"/api/v1/rooms/{room['id']}:start",
            json={"room_version": third_ready["version"]},
            headers={
                **headers("start-hidden-action"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        ).json()
        submitted = first_player.put(
            f"/api/v1/rooms/{room['id']}/rounds/{room['round']}/action",
            json={"text": "這是尚未揭露的行動。", "room_version": started["version"]},
            headers={**headers("hidden-action-1"), "X-CSRF-Token": first["session"]["csrfToken"]},
        )
        observed = second_player.get("/api/v1/rooms/current")

    assert submitted.status_code == 200
    first_in_other_view = next(player for player in observed.json()["players"] if player["name"] == "甲")
    assert first_in_other_view["hasSubmitted"] is True
    assert first_in_other_view["action"] == ""
    assert "這是尚未揭露的行動。" not in observed.text
