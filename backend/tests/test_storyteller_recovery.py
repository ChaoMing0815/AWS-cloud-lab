from copy import deepcopy

import pytest

from app.adapters.memory_idempotency_store import MemoryIdempotencyStore
from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.secure_dice_roller import SecureDiceRoller
from app.adapters.session_security import HmacSessionTokenFactory
from app.application.ports import StorytellerFailure
from app.application.room_service import RoomService
from app.application.security import hash_session_token
from app.domain.models import Character, DiceResult, Player, Room, World


class ScriptedStoryteller:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = list(outcomes)
        self.round_calls: list[Room] = []

    def resolve_round(self, room: Room) -> str:
        self.round_calls.append(deepcopy(room))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return str(outcome)

    def resolve_ending(self, _room: Room) -> str:
        return "測試結局"


def pending_resolution_room() -> Room:
    return Room(
        id="story-recovery-room",
        room_code="STORY1",
        status="RESOLVING",
        version=4,
        round_number=1,
        world=World(
            name="故事復原測試",
            story_title="故事復原測試",
            premise="固定判定後呼叫故事主持人。",
            objective="驗證失敗不污染 canonical state。",
        ),
        host_session_hash=hash_session_token("host-token"),
        host_csrf_token="host-csrf",
        initial_player_count=1,
        players=[
            Player(
                id="player-1",
                name="甲",
                role="測試者",
                action="我整理已知線索。",
                action_approach="insight",
                character=Character(
                    name="角色甲",
                    background="負責驗證故事復原。",
                    trait="冷靜",
                    weakness="謹慎過度",
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
                d6_1=3,
                d6_2=4,
                approach="insight",
                attribute_value=2,
                base_total=9,
                final_total=9,
                result="PARTIAL_SUCCESS",
                progress_delta=1,
                danger_delta=1,
                spark_decision="DECLINE",
            )
        ],
    )


def service_with(storyteller: ScriptedStoryteller) -> tuple[RoomService, MemoryRoomRepository]:
    repository = MemoryRoomRepository()
    service = RoomService(
        repository,
        storyteller,
        MemoryIdempotencyStore(),
        HmacSessionTokenFactory(),
        SecureDiceRoller(),
    )
    repository.save(pending_resolution_room())
    return service, repository


def resolve(service: RoomService) -> Room:
    return service.resolve_round(
        room_id="story-recovery-room",
        round_number=1,
        skip_pending_spark=False,
        expected_version=4,
        host_token="host-token",
        csrf_token="host-csrf",
        idempotency_key="story-recovery-resolve",
    )


@pytest.mark.parametrize("failure_code", ["TIMEOUT", "THROTTLED", "SCHEMA_INVALID"])
def test_retryable_story_failure_retries_once_with_identical_draft(failure_code: str) -> None:
    storyteller = ScriptedStoryteller(
        [StorytellerFailure(failure_code), "第二次嘗試成功的敘事。"]
    )
    service, _repository = service_with(storyteller)

    resolved = resolve(service)

    assert len(storyteller.round_calls) == 2
    assert storyteller.round_calls[0] == storyteller.round_calls[1]
    assert resolved.status == "COLLECTING_ACTIONS"
    assert resolved.progress_points == 1
    assert resolved.danger_points == 1
    assert resolved.entries[-1].text == "第二次嘗試成功的敘事。"
    assert resolved.resolution_attempts == 2
    assert resolved.resolution_mode == "storyteller"
    assert resolved.resolution_failure_code is None


def test_retry_exhaustion_preserves_rules_state_and_records_failure() -> None:
    storyteller = ScriptedStoryteller(
        [StorytellerFailure("TIMEOUT"), StorytellerFailure("TIMEOUT")]
    )
    service, repository = service_with(storyteller)
    before = repository.get("story-recovery-room")

    failed = resolve(service)

    assert before is not None
    assert len(storyteller.round_calls) == 2
    assert failed.status == "RESOLUTION_FAILED"
    assert failed.version == before.version + 1
    assert failed.progress_points == before.progress_points
    assert failed.danger_points == before.danger_points
    assert failed.players[0].character == before.players[0].character
    assert failed.players[0].action == before.players[0].action
    assert failed.entries == before.entries
    assert failed.dice_results == before.dice_results
    assert failed.resolution_attempts == 2
    assert failed.resolution_failure_code == "TIMEOUT"
    assert failed.resolution_mode is None


def test_content_rejection_is_not_retried_and_preserves_rules_state() -> None:
    storyteller = ScriptedStoryteller([StorytellerFailure("CONTENT_REJECTED")])
    service, repository = service_with(storyteller)
    before = repository.get("story-recovery-room")

    failed = resolve(service)

    assert before is not None
    assert len(storyteller.round_calls) == 1
    assert failed.status == "RESOLUTION_FAILED"
    assert failed.progress_points == before.progress_points
    assert failed.danger_points == before.danger_points
    assert failed.entries == before.entries
    assert failed.resolution_attempts == 1
    assert failed.resolution_failure_code == "CONTENT_REJECTED"


def test_host_fallback_commits_fixed_results_once_without_claiming_llm_success() -> None:
    storyteller = ScriptedStoryteller(
        [StorytellerFailure("TIMEOUT"), StorytellerFailure("TIMEOUT")]
    )
    service, _repository = service_with(storyteller)
    failed = resolve(service)

    fallback = service.fallback_round(
        room_id=failed.id,
        round_number=1,
        expected_version=failed.version,
        host_token="host-token",
        csrf_token="host-csrf",
        idempotency_key="story-fallback-submit",
    )
    replay = service.fallback_round(
        room_id=failed.id,
        round_number=1,
        expected_version=failed.version,
        host_token="host-token",
        csrf_token="host-csrf",
        idempotency_key="story-fallback-submit",
    )

    assert fallback.status == "COLLECTING_ACTIONS"
    assert fallback.round_number == 2
    assert fallback.progress_points == 1
    assert fallback.danger_points == 1
    assert fallback.players[0].character is not None
    assert fallback.players[0].character.spark == 1
    assert fallback.players[0].action == ""
    assert fallback.resolution_mode == "fallback"
    assert fallback.resolution_failure_code == "TIMEOUT"
    assert "deterministic fallback" in fallback.entries[-1].text
    assert "部分成功" in fallback.entries[-1].text
    assert replay == fallback
