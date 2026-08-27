from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib
import importlib.util

import pytest

from app.domain.models import Character, DiceResult, Player, Room, StoryEntry, TransferCode, World


NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def _module():
    spec = importlib.util.find_spec("app.domain.story_resolution")
    assert spec is not None, "story resolution domain contract 尚未建立"
    return importlib.import_module("app.domain.story_resolution")


def resolution_room(*, version: int = 7, status: str = "AWAITING_SPARK") -> Room:
    return Room(
        id="room-1",
        room_code="SECRET",
        status=status,
        version=version,
        round_number=2,
        world=World(
            name="霽霧之城",
            story_title="最後的燈火",
            premise="玩家共同尋找燈火。",
            objective="在日出前修復燈塔。",
            opening_scene="港口被霧吞沒。",
            core_obstacle="燈芯已經破裂。",
            tone="hopeful",
        ),
        host_session_hash="host-secret-hash",
        host_csrf_token="host-csrf-secret",
        host_session_expires_at=NOW + timedelta(days=1),
        players=[
            Player(
                id="player-1",
                name="甲",
                role="守燈人",
                action="我收集散落的燈芯。",
                action_approach="insight",
                session_hash="player-secret-hash",
                csrf_token="player-csrf-secret",
                session_expires_at=NOW + timedelta(hours=1),
                transfer_code=TransferCode(
                    code_hash="transfer-secret-hash",
                    issued_at=NOW,
                    expires_at=NOW + timedelta(minutes=10),
                ),
                character=Character(
                    name="艾拉",
                    background="在港邊長大的修復師。",
                    trait="細心",
                    weakness="過度自責",
                    courage=1,
                    insight=2,
                    bond=0,
                    spark=1,
                ),
            )
        ],
        entries=[
            StoryEntry(
                id="entry-public",
                type="narrator",
                title="故事主持人",
                round_number=1,
                text="眾人來到被霧包圍的燈塔。",
            )
        ],
        dice_results=[
            DiceResult(
                player_id="player-1",
                round_number=2,
                d6_1=3,
                d6_2=4,
                approach="insight",
                attribute_value=2,
                base_total=9,
                final_total=9,
                result="PARTIAL_SUCCESS",
                progress_delta=1,
                danger_delta=1,
                spark_decision="PENDING",
            )
        ],
        initial_player_count=1,
    )


def _all_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key).lower()
            yield from _all_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _all_keys(nested)


def test_snapshot_is_sanitized_deeply_owned_and_json_shaped() -> None:
    module = _module()
    room = resolution_room(status="RESOLVING", version=8)

    snapshot = module.build_story_resolution_snapshot(
        room,
        source_room_version=7,
        skip_pending_spark=True,
    )
    sealed = deepcopy(snapshot)
    room.world.name = "external mutation"
    room.players[0].character.background = "external nested mutation"
    room.dice_results[0].result = "FAILURE"

    assert snapshot == sealed
    assert set(snapshot) == {
        "operation",
        "producer",
        "world",
        "canonical_state",
        "recent_story",
        "resolved_actions",
    }
    forbidden = ("session", "csrf", "cookie", "transfer", "token", "hash")
    assert not any(any(term in key for term in forbidden) for key in _all_keys(snapshot))
    assert "host-secret-hash" not in repr(snapshot)
    assert "player-secret-hash" not in repr(snapshot)
    assert snapshot["resolved_actions"][0]["action"] == "我收集散落的燈芯。"


def test_result_fingerprint_is_canonical_and_divergence_is_detectable() -> None:
    module = _module()

    first = {"narration": "霧裡亮起微光。", "meta": {"attempt": 1, "tags": ["a", "b"]}}
    reordered = {"meta": {"tags": ["a", "b"], "attempt": 1}, "narration": "霧裡亮起微光。"}
    changed = {"narration": "另一個結果。", "meta": {"attempt": 1, "tags": ["a", "b"]}}

    assert module.story_result_fingerprint(first) == module.story_result_fingerprint(reordered)
    assert module.story_result_fingerprint(first) != module.story_result_fingerprint(changed)
    assert len(module.story_result_fingerprint(first)) == 64


def test_fingerprint_rejects_non_json_result() -> None:
    module = _module()

    with pytest.raises(ValueError, match="JSON"):
        module.story_result_fingerprint({"not_json": object()})
