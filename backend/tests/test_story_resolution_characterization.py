from copy import deepcopy
from datetime import datetime, timezone

from app.adapters.memory_idempotency_store import MemoryIdempotencyStore
from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.secure_dice_roller import SecureDiceRoller
from app.adapters.session_security import HmacSessionTokenFactory
from app.application.ports import StorytellerFailure
from app.application.room_service import RoomService
from app.application.security import hash_session_token
from app.domain.models import Character, DiceResult, Player, Room, World


class FixedClock:
    def now(self):
        return datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


class ScriptedStoryteller:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.round_calls = []
        self.ending_calls = 0

    def resolve_round(self, room):
        self.round_calls.append(deepcopy(room))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def resolve_ending(self, room):
        self.ending_calls += 1
        return "現行同步結局。"


def _room():
    return Room(
        id="characterization-room",
        room_code="CHAR01",
        status="RESOLVING",
        version=4,
        round_number=1,
        world=World(name="測試", story_title="測試", premise="測試", objective="測試"),
        host_session_hash=hash_session_token("host-token"),
        host_csrf_token="host-csrf",
        expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        host_session_expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        initial_player_count=1,
        players=[
            Player(
                id="p1",
                name="甲",
                role="測試者",
                action="前進",
                action_approach="courage",
                character=Character("A", "B", "C", "D", 2, 1, 0, 1),
            )
        ],
        dice_results=[
            DiceResult("p1", 1, 3, 4, "courage", 2, 9, 9, "PARTIAL_SUCCESS", 1, 1, spark_decision="DECLINE")
        ],
    )


def _service(storyteller):
    repository = MemoryRoomRepository()
    repository.save(_room())
    return RoomService(
        repository,
        storyteller,
        MemoryIdempotencyStore(),
        HmacSessionTokenFactory(),
        SecureDiceRoller(),
        FixedClock(),
        seed_demo_room=False,
    )


def test_sync_resolve_retry_and_public_result_remain_unchanged() -> None:
    storyteller = ScriptedStoryteller([StorytellerFailure("TIMEOUT"), "第二次敲定的故事。"])
    service = _service(storyteller)

    resolved = service.resolve_round(
        "characterization-room", 1, False, 4, "host-token", "host-csrf", "characterization-key"
    )

    assert len(storyteller.round_calls) == 2
    assert storyteller.round_calls[0] == storyteller.round_calls[1]
    assert resolved.status == "COLLECTING_ACTIONS"
    assert resolved.version == 5
    assert resolved.round_number == 2
    assert resolved.progress_points == 1
    assert resolved.danger_points == 1
    assert resolved.entries[-1].text == "第二次敲定的故事。"
    assert resolved.resolution_attempts == 2
    assert resolved.resolution_failure_code is None
    assert resolved.resolution_mode == "storyteller"
    assert storyteller.ending_calls == 0


def test_sync_nonretryable_failure_still_preserves_round_state() -> None:
    service = _service(ScriptedStoryteller([StorytellerFailure("CONTENT_REJECTED")]))

    failed = service.resolve_round(
        "characterization-room", 1, False, 4, "host-token", "host-csrf", "failure-characterization"
    )

    assert failed.status == "RESOLUTION_FAILED"
    assert failed.version == 5
    assert failed.progress_points == 0
    assert failed.danger_points == 0
    assert failed.players[0].action == "前進"
    assert failed.resolution_attempts == 1
    assert failed.resolution_failure_code == "CONTENT_REJECTED"
