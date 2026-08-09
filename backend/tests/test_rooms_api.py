from fastapi.testclient import TestClient

from app.application.security import hash_session_token
from app.domain.models import Character, DiceResult, Player, Room, World
from app.main import create_app


class FixedDiceRoller:
    def __init__(self, values: list[int]) -> None:
        self.values = iter(values)

    def roll_d6(self) -> int:
        return next(self.values)

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


def test_create_room_atomically_creates_host_player_and_replays() -> None:
    payload = {"nickname": "  昭銘  "}
    with TestClient(create_app()) as client:
        first = client.post(
            "/api/v1/rooms",
            json=payload,
            headers=headers("create-host-player"),
        )
        replay = client.post(
            "/api/v1/rooms",
            json=payload,
            headers=headers("create-host-player"),
        )

    assert first.status_code == 201
    assert first.json()["status"] == "DRAFT"
    assert [player["name"] for player in first.json()["players"]] == ["昭銘"]
    assert first.json()["session"]["principalType"] == "player"
    assert first.json()["session"]["isHost"] is True
    assert first.json()["session"]["playerId"] == first.json()["players"][0]["id"]
    assert client.cookies.get("co_story_host")
    assert client.cookies.get("co_story_player")
    assert replay.json()["id"] == first.json()["id"]
    assert replay.json()["players"] == first.json()["players"]


def test_create_room_rejects_invalid_nickname_without_saving_room() -> None:
    app = create_app()
    with TestClient(app) as client:
        invalid = client.post(
            "/api/v1/rooms",
            json={"nickname": "   "},
            headers=headers("invalid-host-name"),
        )

    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "INVALID_NICKNAME"
    assert len(app.state.room_service.repository._rooms) == 1  # 只有隔離的 Demo room


def test_create_room_idempotency_key_cannot_change_host_nickname() -> None:
    with TestClient(create_app()) as client:
        first = client.post(
            "/api/v1/rooms",
            json={"nickname": "昭銘"},
            headers=headers("create-host-reused"),
        )
        reused = client.post(
            "/api/v1/rooms",
            json={"nickname": "洛河"},
            headers=headers("create-host-reused"),
        )

    assert first.status_code == 201
    assert reused.status_code == 422
    assert reused.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


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
        payload = {
            "text": "我先確認門口狀況。",
            "approach": "courage",
            "room_version": started["version"],
        }

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
            json={
                "text": "這是尚未揭露的行動。",
                "approach": "insight",
                "room_version": started["version"],
            },
            headers={**headers("hidden-action-1"), "X-CSRF-Token": first["session"]["csrfToken"]},
        )
        observed = second_player.get("/api/v1/rooms/current")

    assert submitted.status_code == 200
    first_in_other_view = next(player for player in observed.json()["players"] if player["name"] == "甲")
    assert first_in_other_view["hasSubmitted"] is True
    assert first_in_other_view["action"] == ""
    assert "這是尚未揭露的行動。" not in observed.text


def test_host_rolls_fixed_dice_and_reveals_results() -> None:
    app = create_app(FixedDiceRoller([6, 6, 3, 3, 1, 1]))
    with (
        TestClient(app) as host,
        TestClient(app) as first_player,
        TestClient(app) as second_player,
        TestClient(app) as third_player,
    ):
        room = new_lobby(host, "roll-room")
        clients = [first_player, second_player, third_player]
        names = ["甲", "乙", "丙"]
        joins = []
        current = room
        for index, (client, name) in enumerate(zip(clients, names, strict=True), start=1):
            current = client.post(
                f"/api/v1/rooms/{room['id']}/players",
                json={
                    "nickname": name,
                    "role": "調查員",
                    "room_version": current["version"],
                },
                headers=headers(f"roll-join-{index}"),
            ).json()
            joins.append(current)

        for index, (client, joined) in enumerate(zip(clients, joins, strict=True), start=1):
            current = update_character(
                client,
                current,
                joined["session"]["csrfToken"],
                f"roll-character-{index}",
                f"角色{names[index - 1]}",
            )

        started = host.post(
            f"/api/v1/rooms/{room['id']}:start",
            json={"room_version": current["version"]},
            headers={
                **headers("roll-start"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        ).json()

        actions = [
            ("我正面要求查看紀錄。", "courage"),
            ("我檢查備份留下的線索。", "insight"),
            ("我請熟識的同事幫忙。", "bond"),
        ]
        current = started
        for index, (client, joined, action) in enumerate(
            zip(clients, joins, actions, strict=True), start=1
        ):
            response = client.put(
                f"/api/v1/rooms/{room['id']}/rounds/1/action",
                json={
                    "text": action[0],
                    "approach": action[1],
                    "room_version": current["version"],
                },
                headers={
                    **headers(f"roll-action-{index}"),
                    "X-CSRF-Token": joined["session"]["csrfToken"],
                },
            )
            assert response.status_code == 200
            current = response.json()

        assert current["status"] == "AWAITING_HOST"
        before_roll = current["version"]
        roll_url = f"/api/v1/rooms/{room['id']}/rounds/1:roll"
        unauthorized = first_player.post(
            roll_url,
            json={"room_version": before_roll},
            headers={
                **headers("roll-not-host"),
                "X-CSRF-Token": joins[0]["session"]["csrfToken"],
            },
        )
        rolled = host.post(
            roll_url,
            json={"room_version": before_roll},
            headers={
                **headers("roll-valid"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        )
        replay = host.post(
            roll_url,
            json={"room_version": before_roll},
            headers={
                **headers("roll-valid"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        )

        rolled_room = rolled.json()
        resolve_url = f"/api/v1/rooms/{room['id']}/rounds/1:resolve"
        pending_resolve = host.post(
            resolve_url,
            json={
                "skip_pending_spark": False,
                "room_version": rolled_room["version"],
            },
            headers={
                **headers("resolve-pending"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        )
        spark_url = f"/api/v1/rooms/{room['id']}/rounds/1/spark"
        bad_csrf = first_player.put(
            spark_url,
            json={"decision": "USE", "room_version": rolled_room["version"]},
            headers={**headers("spark-bad-csrf"), "X-CSRF-Token": "wrong-token"},
        )
        stale_version = first_player.put(
            spark_url,
            json={"decision": "USE", "room_version": rolled_room["version"] + 99},
            headers={
                **headers("spark-stale-version"),
                "X-CSRF-Token": joins[0]["session"]["csrfToken"],
            },
        )
        first_decision = first_player.put(
            spark_url,
            json={"decision": "USE", "room_version": rolled_room["version"]},
            headers={
                **headers("spark-first-use"),
                "X-CSRF-Token": joins[0]["session"]["csrfToken"],
            },
        )
        first_replay = first_player.put(
            spark_url,
            json={"decision": "USE", "room_version": rolled_room["version"]},
            headers={
                **headers("spark-first-use"),
                "X-CSRF-Token": joins[0]["session"]["csrfToken"],
            },
        )
        repeated_decision = first_player.put(
            spark_url,
            json={"decision": "DECLINE", "room_version": first_decision.json()["version"]},
            headers={
                **headers("spark-first-again"),
                "X-CSRF-Token": joins[0]["session"]["csrfToken"],
            },
        )
        second_decision = second_player.put(
            spark_url,
            json={
                "decision": "DECLINE",
                "room_version": first_decision.json()["version"],
            },
            headers={
                **headers("spark-second-decline"),
                "X-CSRF-Token": joins[1]["session"]["csrfToken"],
            },
        )

        internal_room = app.state.room_service.repository.get(room["id"])
        assert internal_room is not None
        internal_third = next(player for player in internal_room.players if player.name == "丙")
        assert internal_third.character is not None
        internal_third.character.spark = 0
        app.state.room_service.repository.save(internal_room)
        no_spark = third_player.put(
            spark_url,
            json={
                "decision": "USE",
                "room_version": second_decision.json()["version"],
            },
            headers={
                **headers("spark-third-unavailable"),
                "X-CSRF-Token": joins[2]["session"]["csrfToken"],
            },
        )
        restored_room = app.state.room_service.repository.get(room["id"])
        assert restored_room is not None
        restored_third = next(player for player in restored_room.players if player.name == "丙")
        assert restored_third.character is not None
        restored_third.character.spark = 1
        app.state.room_service.repository.save(restored_room)
        third_decision = third_player.put(
            spark_url,
            json={
                "decision": "USE",
                "room_version": second_decision.json()["version"],
            },
            headers={
                **headers("spark-third-use"),
                "X-CSRF-Token": joins[2]["session"]["csrfToken"],
            },
        )
        non_host_resolve = first_player.post(
            resolve_url,
            json={
                "skip_pending_spark": False,
                "room_version": third_decision.json()["version"],
            },
            headers={
                **headers("resolve-not-host"),
                "X-CSRF-Token": joins[0]["session"]["csrfToken"],
            },
        )
        resolved = host.post(
            resolve_url,
            json={
                "skip_pending_spark": False,
                "room_version": third_decision.json()["version"],
            },
            headers={
                **headers("resolve-valid"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        )
        resolve_replay = host.post(
            resolve_url,
            json={
                "skip_pending_spark": False,
                "room_version": third_decision.json()["version"],
            },
            headers={
                **headers("resolve-valid"),
                "X-CSRF-Token": room["session"]["hostCsrfToken"],
            },
        )

    assert unauthorized.status_code == 401
    result = rolled.json()
    assert rolled.status_code == 200
    assert result["status"] == "AWAITING_SPARK"
    assert [item["result"] for item in result["diceResults"]] == [
        "SUCCESS",
        "PARTIAL_SUCCESS",
        "FAILURE",
    ]
    assert [item["finalTotal"] for item in result["diceResults"]] == [14, 7, 2]
    assert result["pendingProgress"] == 3
    assert result["pendingDanger"] == 3
    assert result["progressPoints"] == 0
    assert result["dangerPoints"] == 0
    assert "我正面要求查看紀錄。" in rolled.text
    assert replay.json()["diceResults"] == result["diceResults"]
    assert replay.json()["version"] == result["version"]
    assert pending_resolve.status_code == 409
    assert pending_resolve.json()["error"]["code"] == "SPARK_DECISIONS_PENDING"
    assert bad_csrf.status_code == 403
    assert stale_version.status_code == 409
    assert stale_version.json()["error"]["code"] == "VERSION_CONFLICT"
    assert first_decision.status_code == 200
    assert first_decision.json()["diceResults"][0]["sparkDecision"] == "USE"
    assert first_decision.json()["diceResults"][0]["finalTotal"] == 15
    assert first_replay.json()["version"] == first_decision.json()["version"]
    assert repeated_decision.status_code == 409
    assert repeated_decision.json()["error"]["code"] == "SPARK_ALREADY_DECIDED"
    assert no_spark.status_code == 409
    assert no_spark.json()["error"]["code"] == "SPARK_UNAVAILABLE"
    assert third_decision.json()["status"] == "RESOLVING"
    assert non_host_resolve.status_code == 401
    resolved_room = resolved.json()
    assert resolved.status_code == 200
    assert resolved_room["round"] == 2
    assert resolved_room["status"] == "COLLECTING_ACTIONS"
    assert resolved_room["progressPoints"] == 3
    assert resolved_room["dangerPoints"] == 3
    assert resolved_room["pendingProgress"] == 0
    assert resolved_room["pendingDanger"] == 0
    assert all(not player["hasSubmitted"] for player in resolved_room["players"])
    assert [player["character"]["spark"] for player in resolved_room["players"]] == [0, 1, 1]
    assert resolved_room["diceResults"][0]["sparkUsed"] == 1
    assert "1 次成功、1 次部分成功與 1 次失敗" in resolved_room["entries"][-1]["text"]
    assert resolve_replay.json()["version"] == resolved_room["version"]
    assert resolve_replay.json()["entries"] == resolved_room["entries"]


def test_host_can_explicitly_skip_pending_spark_decisions() -> None:
    app = create_app()
    service = app.state.room_service
    room = Room(
        id="skip-pending-room",
        room_code="SKIP01",
        status="AWAITING_SPARK",
        version=7,
        round_number=1,
        world=World(
            name="測試世界",
            story_title="測試世界",
            premise="驗證房主略過未回應玩家。",
            objective="完成回合結算。",
        ),
        host_session_hash=hash_session_token("host-token"),
        host_csrf_token="host-csrf",
        players=[
            Player(
                id="player-1",
                name="甲",
                role="測試者",
                action="我先觀察現場。",
                action_approach="insight",
                character=Character(
                    name="角色甲",
                    background="測試背景",
                    trait="謹慎",
                    weakness="猶豫",
                    courage=1,
                    insight=2,
                    bond=0,
                    spark=1,
                ),
            )
        ],
        dice_results=[
            DiceResult(
                player_id="player-1",
                round_number=1,
                d6_1=2,
                d6_2=2,
                approach="insight",
                attribute_value=2,
                base_total=6,
                final_total=6,
                result="FAILURE",
                progress_delta=0,
                danger_delta=2,
            )
        ],
    )
    service.repository.save(room)

    resolved = service.resolve_round(
        room_id=room.id,
        round_number=1,
        skip_pending_spark=True,
        expected_version=room.version,
        host_token="host-token",
        csrf_token="host-csrf",
        idempotency_key="skip-pending-resolve",
    )

    assert resolved.dice_results[0].spark_decision == "DECLINE"
    assert resolved.danger_points == 2
    assert resolved.players[0].character is not None
    assert resolved.players[0].character.spark == 2
    assert resolved.players[0].action == ""
    assert resolved.round_number == 2
    assert resolved.status == "COLLECTING_ACTIONS"
