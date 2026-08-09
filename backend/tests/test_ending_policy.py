from fastapi.testclient import TestClient

from app.api.serialization import room_response
from app.application.security import hash_session_token
from app.domain.models import Character, DiceResult, Player, Room, World
from app.main import create_app


def resolving_room(
    *,
    room_id: str,
    round_number: int,
    max_rounds: int,
    progress_points: int,
    danger_points: int,
    result: str,
    progress_delta: int,
    danger_delta: int,
) -> Room:
    player = Player(
        id="player-1",
        name="甲",
        role="測試者",
        action="完成這一回合的行動。",
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
    return Room(
        id=room_id,
        room_code="ENDING",
        status="RESOLVING",
        version=7,
        round_number=round_number,
        world=World(
            name="結局測試世界",
            story_title="結局測試世界",
            premise="驗證回合上限與提前完成。",
            objective="在期限前完成共同目標。",
        ),
        host_session_hash=hash_session_token("host-token"),
        host_csrf_token="host-csrf",
        max_rounds=max_rounds,
        initial_player_count=3,
        progress_points=progress_points,
        danger_points=danger_points,
        players=[player],
        dice_results=[
            DiceResult(
                player_id=player.id,
                round_number=round_number,
                d6_1=3,
                d6_2=3,
                approach="insight",
                attribute_value=2,
                base_total=8,
                final_total=8,
                result=result,
                progress_delta=progress_delta,
                danger_delta=danger_delta,
                spark_decision="DECLINE",
            )
        ],
    )


def resolve(room: Room) -> Room:
    service = create_app().state.room_service
    service.repository.save(room)
    return service.resolve_round(
        room_id=room.id,
        round_number=room.round_number,
        skip_pending_spark=False,
        expected_version=room.version,
        host_token="host-token",
        csrf_token="host-csrf",
        idempotency_key=f"resolve-{room.id}",
    )


def test_last_round_completes_with_partial_success_and_significant_cost() -> None:
    resolved = resolve(
        resolving_room(
            room_id="last-round",
            round_number=4,
            max_rounds=4,
            progress_points=10,
            danger_points=7,
            result="PARTIAL_SUCCESS",
            progress_delta=1,
            danger_delta=1,
        )
    )

    assert resolved.status == "COMPLETED"
    assert resolved.round_number == 4
    assert resolved.ending_result == "PARTIAL_SUCCESS"
    assert resolved.ending_cost == "SIGNIFICANT"
    response = room_response(resolved, {})
    assert response["progressPercent"] == 61
    assert response["dangerPercent"] == 44
    assert response["endingResult"] == "PARTIAL_SUCCESS"
    assert response["endingCost"] == "SIGNIFICANT"
    assert response["entries"][-1]["type"] == "ending"
    assert "部分成功" in response["entries"][-1]["text"]


def test_reaching_100_percent_before_last_round_waits_for_host_choice() -> None:
    resolved = resolve(
        resolving_room(
            room_id="early-success",
            round_number=2,
            max_rounds=4,
            progress_points=16,
            danger_points=0,
            result="SUCCESS",
            progress_delta=2,
            danger_delta=0,
        )
    )

    assert resolved.status == "COMPLETION_AVAILABLE"
    assert resolved.round_number == 3
    assert resolved.ending_result is None
    assert room_response(resolved, {})["progressPercent"] == 100


def test_unfinished_non_final_round_continues_and_serializes_percentages() -> None:
    resolved = resolve(
        resolving_room(
            room_id="continue-round",
            round_number=2,
            max_rounds=4,
            progress_points=10,
            danger_points=0,
            result="SUCCESS",
            progress_delta=2,
            danger_delta=0,
        )
    )

    assert resolved.status == "COLLECTING_ACTIONS"
    assert resolved.round_number == 3
    response = room_response(resolved, {})
    assert response.get("targetPoints") == 18
    assert response.get("progressPercent") == 67
    assert response.get("dangerPercent") == 0
    assert response.get("endingResult") is None


def completion_available_room(room_id: str = "completion-choice") -> Room:
    room = resolving_room(
        room_id=room_id,
        round_number=3,
        max_rounds=4,
        progress_points=18,
        danger_points=9,
        result="SUCCESS",
        progress_delta=0,
        danger_delta=0,
    )
    room.status = "COMPLETION_AVAILABLE"
    room.dice_results = []
    return room


def finish_headers(key: str, csrf: str = "host-csrf") -> dict[str, str]:
    return {"Idempotency-Key": key, "X-CSRF-Token": csrf}


def test_host_can_finish_early_with_idempotent_full_success_ending() -> None:
    app = create_app()
    room = completion_available_room()
    app.state.room_service.repository.save(room)
    with TestClient(app) as host:
        host.cookies.set("co_story_host", "host-token")
        response = host.post(
            f"/api/v1/rooms/{room.id}:finish",
            json={"decision": "FINISH_NOW", "room_version": room.version},
            headers=finish_headers("finish-now-0001"),
        )
        replay = host.post(
            f"/api/v1/rooms/{room.id}:finish",
            json={"decision": "FINISH_NOW", "room_version": room.version},
            headers=finish_headers("finish-now-0001"),
        )

    assert response.status_code == 200
    finished = response.json()
    assert finished["status"] == "COMPLETED"
    assert finished["endingResult"] == "FULL_SUCCESS"
    assert finished["endingCost"] == "SIGNIFICANT"
    assert finished["entries"][-1]["type"] == "ending"
    assert "完整成功" in finished["entries"][-1]["text"]
    assert replay.json()["version"] == finished["version"]
    assert replay.json()["entries"] == finished["entries"]


def test_host_can_continue_epilogue_with_success_locked() -> None:
    app = create_app()
    room = completion_available_room("continue-epilogue")
    app.state.room_service.repository.save(room)
    with TestClient(app) as host:
        host.cookies.set("co_story_host", "host-token")
        response = host.post(
            f"/api/v1/rooms/{room.id}:finish",
            json={"decision": "CONTINUE", "room_version": room.version},
            headers=finish_headers("continue-epilogue-0001"),
        )

    assert response.status_code == 200
    continued = response.json()
    assert continued["status"] == "COLLECTING_ACTIONS"
    assert continued["round"] == 3
    assert continued["successLocked"] is True
    assert continued["endingResult"] is None


def test_finish_requires_host_csrf_and_completion_available_state() -> None:
    app = create_app()
    available = completion_available_room("finish-security")
    wrong_state = completion_available_room("finish-wrong-state")
    wrong_state.status = "COLLECTING_ACTIONS"
    app.state.room_service.repository.save(available)
    app.state.room_service.repository.save(wrong_state)
    with TestClient(app) as host, TestClient(app) as outsider:
        host.cookies.set("co_story_host", "host-token")
        no_host = outsider.post(
            f"/api/v1/rooms/{available.id}:finish",
            json={"decision": "FINISH_NOW", "room_version": available.version},
            headers=finish_headers("finish-no-host-0001"),
        )
        bad_csrf = host.post(
            f"/api/v1/rooms/{available.id}:finish",
            json={"decision": "FINISH_NOW", "room_version": available.version},
            headers=finish_headers("finish-bad-csrf-0001", "wrong-csrf"),
        )
        invalid_state = host.post(
            f"/api/v1/rooms/{wrong_state.id}:finish",
            json={"decision": "FINISH_NOW", "room_version": wrong_state.version},
            headers=finish_headers("finish-wrong-state-0001"),
        )

    assert no_host.status_code == 401
    assert no_host.json()["error"]["code"] == "HOST_SESSION_REQUIRED"
    assert bad_csrf.status_code == 403
    assert bad_csrf.json()["error"]["code"] == "CSRF_FAILED"
    assert invalid_state.status_code == 409
    assert invalid_state.json()["error"]["code"] == "FINISH_NOT_ALLOWED"
