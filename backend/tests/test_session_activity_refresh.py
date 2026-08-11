from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.memory_idempotency_store import MemoryIdempotencyStore
from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.mock_storyteller import MockStoryteller
from app.adapters.secure_dice_roller import SecureDiceRoller
from app.adapters.session_security import HmacSessionTokenFactory
from app.application.ports import StorytellerFailure
from app.application.room_service import RoomService
from app.domain.errors import DomainError
from app.domain.models import Character, DiceResult, Player


class MutableClock:
    def __init__(self, now: datetime) -> None:
        self.now_value = now

    def now(self) -> datetime:
        return self.now_value


@dataclass
class ServiceContext:
    service: RoomService
    repository: MemoryRoomRepository
    clock: MutableClock


NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
WORLD = {
    "story_title": "午夜便利商店大作戰",
    "premise": "盤點資料消失。",
    "objective": "找回資料。",
    "opening_scene": "門市忽然斷電。",
    "core_obstacle": "備份被鎖住。",
    "tone": "slice_of_life",
    "custom_tone": None,
}
CHARACTER = Character(
    name="夜班調查員",
    background="熟悉門市。",
    trait="冷靜",
    weakness="猶豫",
    courage=2,
    insight=1,
    bond=0,
)


def _context(storyteller=None) -> ServiceContext:
    clock = MutableClock(NOW)
    repository = MemoryRoomRepository()
    return ServiceContext(
        service=RoomService(
            repository,
            storyteller or MockStoryteller(),
            MemoryIdempotencyStore(),
            HmacSessionTokenFactory(secret=b"activity-refresh-test-secret"),
            SecureDiceRoller(),
            clock=clock,
        ),
        repository=repository,
        clock=clock,
    )


def _draft(context: ServiceContext):
    return context.service.create_room("房主", "create-activity-refresh")


def _set_lobby(context: ServiceContext, room_id: str):
    room = context.repository.get(room_id)
    assert room is not None
    room.status = "LOBBY"
    context.repository.save(room)
    return room


def _set_collecting_actions(context: ServiceContext, room_id: str):
    room = context.repository.get(room_id)
    assert room is not None
    room.status = "COLLECTING_ACTIONS"
    room.players[0].character = CHARACTER
    room.players.append(
        Player(
            id="other-player",
            name="其他玩家",
            role="共同創作者",
            session_expires_at=room.players[0].session_expires_at,
            character=CHARACTER,
        )
    )
    context.repository.save(room)
    return room


def _add_other_players(room, count: int = 2) -> None:
    for index in range(count):
        room.players.append(
            Player(
                id=f"other-player-{index}",
                name=f"其他玩家{index}",
                role="共同創作者",
                session_expires_at=room.players[0].session_expires_at,
                character=CHARACTER,
            )
        )


def _advance_to_activity(context: ServiceContext) -> datetime:
    context.clock.now_value += timedelta(hours=1)
    return context.clock.now() + timedelta(days=7)


def _assert_actor_refreshes_without_cross_session_changes(
    room,
    expected: datetime,
    actor_expiry: datetime | None,
    unchanged_expiries: tuple[datetime | None, ...],
    original_expiries: tuple[datetime | None, ...],
) -> None:
    assert room.expires_at == expected
    assert actor_expiry == expected
    assert unchanged_expiries == original_expiries


def test_successful_join_refreshes_room_and_joining_player_only() -> None:
    context = _context()
    room, _, _ = _draft(context)
    room = _set_lobby(context, room.id)
    original_host_expiry = room.host_session_expires_at
    original_host_player_expiry = room.players[0].session_expires_at
    context.clock.now_value += timedelta(hours=1)

    joined, _ = context.service.join_room(
        room.id,
        "新玩家",
        "企劃",
        room.version,
        "join-activity-refresh",
    )

    expected = context.clock.now() + timedelta(days=7)
    joining_player = next(player for player in joined.players if player.name == "新玩家")
    assert joined.expires_at == expected
    assert joining_player.session_expires_at == expected
    assert joined.host_session_expires_at == original_host_expiry
    assert joined.players[0].session_expires_at == original_host_player_expiry


def test_successful_confirm_world_refreshes_room_and_host_only_and_replay_does_not_drift() -> None:
    context = _context()
    room, host_token, _ = _draft(context)
    original_player_expiry = room.players[0].session_expires_at
    context.clock.now_value += timedelta(hours=1)

    confirmed = context.service.confirm_world(
        room.id,
        WORLD,
        6,
        room.version,
        host_token,
        room.host_csrf_token,
        "confirm-activity-refresh",
    )
    expected = context.clock.now() + timedelta(days=7)
    assert confirmed.expires_at == expected
    assert confirmed.host_session_expires_at == expected
    assert confirmed.players[0].session_expires_at == original_player_expiry

    context.clock.now_value += timedelta(hours=2)
    replay = context.service.confirm_world(
        room.id,
        WORLD,
        6,
        room.version,
        host_token,
        room.host_csrf_token,
        "confirm-activity-refresh",
    )
    assert replay.expires_at == expected
    assert replay.host_session_expires_at == expected


def test_successful_submit_action_refreshes_room_and_actor_only() -> None:
    context = _context()
    room, _, player_token = _draft(context)
    room = _set_collecting_actions(context, room.id)
    original_host_expiry = room.host_session_expires_at
    original_other_player_expiry = room.players[1].session_expires_at
    context.clock.now_value += timedelta(hours=1)

    updated = context.service.submit_action(
        room.id,
        room.round_number,
        "我檢查備份紀錄。",
        "insight",
        room.version,
        player_token,
        room.players[0].csrf_token,
        "action-activity-refresh",
    )

    expected = context.clock.now() + timedelta(days=7)
    assert updated.expires_at == expected
    assert updated.players[0].session_expires_at == expected
    assert updated.host_session_expires_at == original_host_expiry
    assert updated.players[1].session_expires_at == original_other_player_expiry


def test_join_by_code_refreshes_room_and_joining_player_only() -> None:
    context = _context()
    room, _, _ = _draft(context)
    room = _set_lobby(context, room.id)
    original_expiries = (room.host_session_expires_at, room.players[0].session_expires_at)
    expected = _advance_to_activity(context)

    joined, _ = context.service.join_room_by_code(
        room.room_code,
        "代碼玩家",
        "join-code-activity-refresh",
    )

    joining_player = next(player for player in joined.players if player.name == "代碼玩家")
    _assert_actor_refreshes_without_cross_session_changes(
        joined,
        expected,
        joining_player.session_expires_at,
        (joined.host_session_expires_at, joined.players[0].session_expires_at),
        original_expiries,
    )


def test_start_game_refreshes_room_and_host_only() -> None:
    context = _context()
    room, host_token, _ = _draft(context)
    room = _set_lobby(context, room.id)
    room.players[0].character = CHARACTER
    _add_other_players(room)
    context.repository.save(room)
    original_player_expiries = tuple(player.session_expires_at for player in room.players)
    expected = _advance_to_activity(context)

    started = context.service.start_game(
        room.id,
        room.version,
        host_token,
        room.host_csrf_token,
        "start-activity-refresh",
    )

    _assert_actor_refreshes_without_cross_session_changes(
        started,
        expected,
        started.host_session_expires_at,
        tuple(player.session_expires_at for player in started.players),
        original_player_expiries,
    )


def _awaiting_host_room(context: ServiceContext):
    room, host_token, player_token = _draft(context)
    room.status = "AWAITING_HOST"
    room.initial_player_count = 3
    room.players[0].character = CHARACTER
    room.players[0].action = "我核對資料。"
    room.players[0].action_approach = "insight"
    _add_other_players(room)
    for player in room.players[1:]:
        player.action = "我協助核對。"
        player.action_approach = "insight"
    context.repository.save(room)
    return room, host_token, player_token


def test_roll_round_refreshes_room_and_host_only() -> None:
    context = _context()
    room, host_token, _ = _awaiting_host_room(context)
    original_player_expiries = tuple(player.session_expires_at for player in room.players)
    expected = _advance_to_activity(context)

    rolled = context.service.roll_round(
        room.id,
        room.round_number,
        room.version,
        host_token,
        room.host_csrf_token,
        "roll-activity-refresh",
    )

    _assert_actor_refreshes_without_cross_session_changes(
        rolled,
        expected,
        rolled.host_session_expires_at,
        tuple(player.session_expires_at for player in rolled.players),
        original_player_expiries,
    )


def _awaiting_spark_room(context: ServiceContext):
    room, host_token, player_token = _draft(context)
    room.status = "AWAITING_SPARK"
    room.initial_player_count = 3
    room.players[0].character = CHARACTER
    _add_other_players(room)
    room.dice_results.append(
        DiceResult(
            player_id=room.players[0].id,
            round_number=room.round_number,
            d6_1=3,
            d6_2=4,
            approach="insight",
            attribute_value=1,
            base_total=8,
            final_total=8,
            result="PARTIAL_SUCCESS",
            progress_delta=1,
            danger_delta=0,
        )
    )
    context.repository.save(room)
    return room, host_token, player_token


def test_decide_spark_refreshes_room_and_deciding_player_only() -> None:
    context = _context()
    room, _, player_token = _awaiting_spark_room(context)
    original_expiries = (
        room.host_session_expires_at,
        room.players[1].session_expires_at,
        room.players[2].session_expires_at,
    )
    expected = _advance_to_activity(context)

    decided = context.service.decide_spark(
        room.id,
        room.round_number,
        "DECLINE",
        room.version,
        player_token,
        room.players[0].csrf_token,
        "spark-activity-refresh",
    )

    _assert_actor_refreshes_without_cross_session_changes(
        decided,
        expected,
        decided.players[0].session_expires_at,
        (
            decided.host_session_expires_at,
            decided.players[1].session_expires_at,
            decided.players[2].session_expires_at,
        ),
        original_expiries,
    )


def _resolvable_room(context: ServiceContext):
    room, host_token, player_token = _awaiting_spark_room(context)
    room.dice_results[0].spark_decision = "DECLINE"
    context.repository.save(room)
    return room, host_token, player_token


def test_resolve_round_refreshes_room_and_host_only() -> None:
    context = _context()
    room, host_token, _ = _resolvable_room(context)
    original_player_expiries = tuple(player.session_expires_at for player in room.players)
    expected = _advance_to_activity(context)

    resolved = context.service.resolve_round(
        room.id,
        room.round_number,
        False,
        room.version,
        host_token,
        room.host_csrf_token,
        "resolve-activity-refresh",
    )

    _assert_actor_refreshes_without_cross_session_changes(
        resolved,
        expected,
        resolved.host_session_expires_at,
        tuple(player.session_expires_at for player in resolved.players),
        original_player_expiries,
    )


class AlwaysFailingStoryteller(MockStoryteller):
    def resolve_round(self, room):
        raise StorytellerFailure("TIMEOUT")


def test_resolution_failure_save_path_refreshes_room_and_host_only() -> None:
    context = _context(AlwaysFailingStoryteller())
    room, host_token, _ = _resolvable_room(context)
    original_player_expiries = tuple(player.session_expires_at for player in room.players)
    expected = _advance_to_activity(context)

    failed = context.service.resolve_round(
        room.id,
        room.round_number,
        False,
        room.version,
        host_token,
        room.host_csrf_token,
        "resolution-failure-activity-refresh",
    )

    assert failed.status == "RESOLUTION_FAILED"
    _assert_actor_refreshes_without_cross_session_changes(
        failed,
        expected,
        failed.host_session_expires_at,
        tuple(player.session_expires_at for player in failed.players),
        original_player_expiries,
    )


def test_fallback_round_refreshes_room_and_host_only() -> None:
    context = _context()
    room, host_token, _ = _resolvable_room(context)
    room.status = "RESOLUTION_FAILED"
    context.repository.save(room)
    original_player_expiries = tuple(player.session_expires_at for player in room.players)
    expected = _advance_to_activity(context)

    resolved = context.service.fallback_round(
        room.id,
        room.round_number,
        room.version,
        host_token,
        room.host_csrf_token,
        "fallback-activity-refresh",
    )

    _assert_actor_refreshes_without_cross_session_changes(
        resolved,
        expected,
        resolved.host_session_expires_at,
        tuple(player.session_expires_at for player in resolved.players),
        original_player_expiries,
    )


def test_update_character_is_not_an_activity_refresh_allowlist_member() -> None:
    context = _context()
    room, _, player_token = _draft(context)
    room = _set_lobby(context, room.id)
    original_expiries = (
        room.expires_at,
        room.host_session_expires_at,
        room.players[0].session_expires_at,
    )
    _advance_to_activity(context)

    updated = context.service.update_character(
        room.id,
        {
            "name": "調查員",
            "background": "熟悉門市。",
            "trait": "冷靜",
            "weakness": "猶豫",
            "courage": 2,
            "insight": 1,
            "bond": 0,
        },
        room.version,
        player_token,
        room.players[0].csrf_token,
        "character-not-activity-refresh",
    )

    assert (
        updated.expires_at,
        updated.host_session_expires_at,
        updated.players[0].session_expires_at,
    ) == original_expiries


@pytest.mark.parametrize("kind", ("stale", "illegal"))
def test_stale_or_illegal_mutation_never_refreshes_expiry(kind: str) -> None:
    context = _context()
    room, host_token, player_token = _draft(context)
    original_expiries = (
        room.expires_at,
        room.host_session_expires_at,
        room.players[0].session_expires_at,
    )
    context.clock.now_value += timedelta(hours=1)

    if kind == "stale":
        with pytest.raises(DomainError) as error:
            context.service.confirm_world(
                room.id,
                WORLD,
                6,
                room.version - 1,
                host_token,
                room.host_csrf_token,
                "stale-activity-refresh",
            )
        assert error.value.code == "VERSION_CONFLICT"
    else:
        with pytest.raises(DomainError) as error:
            context.service.submit_action(
                room.id,
                room.round_number,
                "我不該能提交這個行動。",
                "insight",
                room.version,
                player_token,
                room.players[0].csrf_token,
                "illegal-activity-refresh",
            )
        assert error.value.code == "ACTION_NOT_ALLOWED"

    persisted = context.repository.get(room.id)
    assert persisted is not None
    assert (
        persisted.expires_at,
        persisted.host_session_expires_at,
        persisted.players[0].session_expires_at,
    ) == original_expiries


def test_completed_room_uses_completion_expiry_caps_host_and_replay_does_not_drift() -> None:
    context = _context()
    room, host_token, _ = _draft(context)
    room.status = "COMPLETION_AVAILABLE"
    room.initial_player_count = 3
    room.host_session_expires_at = NOW + timedelta(days=14)
    context.repository.save(room)
    context.clock.now_value += timedelta(hours=1)

    completed = context.service.finish_game(
        room.id,
        "END",
        room.version,
        host_token,
        room.host_csrf_token,
        "finish-activity-refresh",
    )
    expected = context.clock.now() + timedelta(days=7)
    assert completed.status == "COMPLETED"
    assert completed.expires_at == expected
    assert completed.host_session_expires_at == expected

    context.clock.now_value += timedelta(hours=2)
    replay = context.service.finish_game(
        room.id,
        "END",
        room.version,
        host_token,
        room.host_csrf_token,
        "finish-activity-refresh",
    )
    assert replay.expires_at == expected
    assert replay.host_session_expires_at == expected
