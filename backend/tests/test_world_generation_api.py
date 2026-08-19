from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient

from app.application.ports import StorytellerFailure
from app.domain.models import World
from app.main import create_app


WORLD_CONFIRMATION = {
    "story_title": "午夜便利商店大作戰",
    "premise": "三位夜班夥伴發現年度盤點資料離奇消失，店長將在天亮前抵達並檢查所有紀錄；若無法及時找回，全體都得留下重新盤點整間門市。",
    "objective": "在店長抵達前找回盤點資料並完成正確報表。",
    "opening_scene": "凌晨兩點，收銀機突然重開機，唯一的盤點檔案也從共用資料夾消失了。",
    "core_obstacle": "備份硬碟被鎖在倉庫，而唯一知道密碼的前任店員已經離職。",
    "tone": "slice_of_life",
    "custom_tone": None,
    "max_rounds": 6,
}
GENERATION_PAYLOAD = {
    "keywords": [" 夜班 ", " 便利商店", "盤點 "],
    "tone": "mystery",
    "custom_tone": None,
    "supplemental_request": "請讓玩家能編輯後再確認。",
}


class WorldGenerationStoryteller:
    def __init__(self, outcome=None) -> None:
        self.outcome = outcome
        self.calls: list[dict] = []

    def generate_world(self, keywords, tone, custom_tone, supplemental_request) -> World:
        self.calls.append(
            {
                "keywords": deepcopy(keywords),
                "tone": tone,
                "custom_tone": custom_tone,
                "supplemental_request": supplemental_request,
            }
        )
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return World(
            name="夜班盤點迷蹤",
            story_title="夜班盤點迷蹤",
            premise="凌晨的盤點資料忽然消失，夜班夥伴必須在店長抵達前找到被改寫的紀錄。",
            objective="找回正確盤點資料並交出可驗證報表。",
            opening_scene="收銀機重啟後，所有交班紀錄都變成空白。",
            core_obstacle="備份硬碟被鎖在倉庫深處，而密碼只留下一半線索。",
            tone=tone,
            custom_tone=custom_tone,
        )

    def resolve_round(self, _room) -> str:
        return "測試敘事"

    def resolve_ending(self, _room) -> str:
        return "測試結局"


def create_room(client: TestClient, key: str = "world-generation-create") -> dict:
    response = client.post(
        "/api/v1/rooms",
        json={"nickname": "房主"},
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 201
    return response.json()


def generate_world(client: TestClient, room: dict, key: str, **overrides) -> object:
    payload = {**GENERATION_PAYLOAD, **overrides, "room_version": room["version"]}
    return client.post(
        f"/api/v1/rooms/{room['id']}/world:generate",
        json=payload,
        headers={
            "Idempotency-Key": key,
            "X-CSRF-Token": room["session"]["hostCsrfToken"],
        },
    )


def confirm_world(client: TestClient, room: dict) -> dict:
    response = client.put(
        f"/api/v1/rooms/{room['id']}/world",
        json={**WORLD_CONFIRMATION, "room_version": room["version"]},
        headers={
            "Idempotency-Key": "confirm-generated-world",
            "X-CSRF-Token": room["session"]["hostCsrfToken"],
        },
    )
    assert response.status_code == 200
    return response.json()


def test_host_generates_editable_draft_once_and_idempotency_replay_does_not_reinvoke() -> None:
    storyteller = WorldGenerationStoryteller()
    with TestClient(create_app(storyteller=storyteller)) as client:
        created = create_room(client)
        first = generate_world(client, created, "world-generation-replay")
        replay = generate_world(client, created, "world-generation-replay")

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert first.json()["status"] == "DRAFT"
    assert first.json()["version"] == created["version"] + 1
    assert first.json()["world"]["storyTitle"] == "夜班盤點迷蹤"
    assert first.json()["worldGenerationCount"] == 1
    assert storyteller.calls == [
        {
            "keywords": ["夜班", "便利商店", "盤點"],
            "tone": "mystery",
            "custom_tone": None,
            "supplemental_request": "請讓玩家能編輯後再確認。",
        }
    ]


def test_default_mock_generated_draft_can_be_confirmed_without_manual_repair() -> None:
    with TestClient(create_app()) as client:
        created = create_room(client, "mock-generated-world-create")
        generated = generate_world(client, created, "mock-generated-world-generate")

        assert generated.status_code == 200
        draft = generated.json()["world"]
        confirmed = client.put(
            f"/api/v1/rooms/{created['id']}/world",
            json={
                "story_title": draft["storyTitle"],
                "premise": draft["premise"],
                "objective": draft["objective"],
                "opening_scene": draft["openingScene"],
                "core_obstacle": draft["coreObstacle"],
                "tone": draft["tone"],
                "custom_tone": draft["customTone"],
                "max_rounds": 6,
                "room_version": generated.json()["version"],
            },
            headers={
                "Idempotency-Key": "mock-generated-world-confirm",
                "X-CSRF-Token": created["session"]["hostCsrfToken"],
            },
        )

    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "LOBBY"


@pytest.mark.parametrize(
    "overrides",
    [
        {"keywords": ["只有", "兩個"]},
        {"keywords": ["一", "二", "三", "四", "五", "六"]},
        {"keywords": [" ", "便利商店", "盤點"]},
        {"keywords": ["超" * 21, "便利商店", "盤點"]},
        {"tone": "custom", "custom_tone": None},
        {"tone": "mystery", "custom_tone": "不應接受"},
        {"supplemental_request": "x" * 201},
    ],
)
def test_world_generation_validates_keyword_and_tone_contract_before_storyteller(overrides) -> None:
    storyteller = WorldGenerationStoryteller()
    with TestClient(create_app(storyteller=storyteller)) as client:
        room = create_room(client, "world-generation-validation-create")
        response = generate_world(client, room, "world-generation-validation", **overrides)

    assert response.status_code == 422
    assert storyteller.calls == []


def test_world_generation_allows_only_two_actual_storyteller_invocations() -> None:
    storyteller = WorldGenerationStoryteller()
    with TestClient(create_app(storyteller=storyteller)) as client:
        room = create_room(client, "world-generation-limit-create")
        first = generate_world(client, room, "world-generation-limit-01")
        assert first.status_code == 200
        second = generate_world(client, first.json(), "world-generation-limit-02")
        assert second.status_code == 200
        third = generate_world(client, second.json(), "world-generation-limit-03")

    assert third.status_code == 409
    assert len(storyteller.calls) == 2


@pytest.mark.parametrize(
    ("failure", "expected_status"),
    [
        (StorytellerFailure("TIMEOUT"), 503),
        (StorytellerFailure("CONTENT_REJECTED"), 422),
    ],
)
def test_world_generation_failure_consumes_attempt_and_replay_does_not_leak_or_reinvoke(
    failure, expected_status, caplog
) -> None:
    storyteller = WorldGenerationStoryteller(failure)
    app = create_app(storyteller=storyteller)
    caplog.set_level("WARNING", logger="co_story.storyteller")
    with TestClient(app) as client:
        room = create_room(client, "world-generation-failure-create")
        first = generate_world(client, room, "world-generation-failure")
        replay = generate_world(client, room, "world-generation-failure")

    assert first.status_code == expected_status
    assert replay.status_code == expected_status
    assert "請讓玩家能編輯後再確認" not in first.text
    assert "TIMEOUT" not in first.text
    assert "CONTENT_REJECTED" not in first.text
    assert len(storyteller.calls) == 1
    stored = app.state.room_service.repository.get(room["id"])
    assert stored.world_generation_count == 1
    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "co_story.storyteller"
    ]
    assert events == [
        {"operation": "generate_world", "failure_code": failure.code}
    ]
    assert "請讓玩家能編輯後再確認" not in caplog.text


def test_non_host_cannot_generate_world_or_invoke_storyteller() -> None:
    storyteller = WorldGenerationStoryteller()
    app = create_app(storyteller=storyteller)
    with TestClient(app) as host, TestClient(app) as outsider:
        room = create_room(host, "world-generation-non-host-create")
        outsider.cookies.set("co_story_local_room", room["id"])
        response = generate_world(outsider, room, "world-generation-non-host")

    assert response.status_code == 401
    assert storyteller.calls == []


def test_confirmed_world_cannot_be_generated_again() -> None:
    storyteller = WorldGenerationStoryteller()
    with TestClient(create_app(storyteller=storyteller)) as client:
        created = create_room(client, "world-generation-confirmed-create")
        confirmed = confirm_world(client, created)
        response = generate_world(client, confirmed, "world-generation-confirmed")

    assert response.status_code == 409
    assert storyteller.calls == []
