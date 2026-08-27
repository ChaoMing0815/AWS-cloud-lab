from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

from app.application.ports import StoryResolutionNarrator, Storyteller, StorytellerFailure
from app.application.story_resolution import apply_story_result
from app.domain.models import Character, DiceResult, Player, Room, StoryEntry, World


class StorytellerSnapshotNarrator(StoryResolutionNarrator):
    """Runs the existing storyteller against a session-free immutable snapshot."""

    def __init__(self, storyteller: Storyteller) -> None:
        self._storyteller = storyteller

    def resolve(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        try:
            room = _room_from_snapshot(deepcopy(snapshot))
            narration = self._storyteller.resolve_round(room)
            result = {"narration": narration}
            simulated = deepcopy(room)
            _, completed = apply_story_result(
                simulated,
                result,
                entry_id_factory=lambda: str(uuid4()),
                ending_narration_factory=self._storyteller.resolve_ending,
            )
            if completed:
                result["ending_narration"] = simulated.entries[-1].text
            return result
        except StorytellerFailure:
            raise
        except (KeyError, TypeError, ValueError):
            raise StorytellerFailure("SCHEMA_INVALID") from None


def _room_from_snapshot(snapshot: dict[str, Any]) -> Room:
    if set(snapshot) != {
        "operation",
        "producer",
        "world",
        "canonical_state",
        "recent_story",
        "resolved_actions",
    } or snapshot["operation"] != "resolve-round":
        raise ValueError("unsupported story snapshot")
    state = snapshot["canonical_state"]
    world_data = snapshot["world"]
    round_number = _positive_int(state["round_number"])
    max_rounds = _positive_int(state["max_rounds"])
    players: list[Player] = []
    dice_results: list[DiceResult] = []
    seen_player_ids: set[str] = set()
    for action in snapshot["resolved_actions"]:
        player_id = _required_text(action["player_id"])
        if player_id in seen_player_ids:
            raise ValueError("duplicate player in snapshot")
        seen_player_ids.add(player_id)
        character_data = action["character"]
        if not isinstance(character_data, dict):
            raise ValueError("character is required")
        player = Player(
            id=player_id,
            name=_required_text(action["player_name"]),
            role=_required_text(action["role"]),
            action=_required_text(action["action"]),
            action_approach=_required_text(action["approach"]),
            character=Character(**character_data),
        )
        dice = action["dice"]
        players.append(player)
        dice_results.append(
            DiceResult(
                player_id=player_id,
                round_number=round_number,
                d6_1=dice["d6_1"],
                d6_2=dice["d6_2"],
                approach=action["approach"],
                attribute_value=dice["attribute_value"],
                base_total=dice["base_total"],
                final_total=dice["final_total"],
                result=dice["result"],
                progress_delta=dice["progress_delta"],
                danger_delta=dice["danger_delta"],
                spark_used=dice["spark_used"],
                spark_decision=dice["spark_decision"],
            )
        )
    if not players:
        raise ValueError("resolved actions are required")
    entries = [
        StoryEntry(
            id=f"snapshot-entry-{index}",
            type=_required_text(entry["type"]),
            title=_required_text(entry["title"]),
            round_number=_positive_int(entry["round_number"]),
            text=_required_text(entry["text"]),
        )
        for index, entry in enumerate(snapshot["recent_story"], start=1)
    ]
    return Room(
        id="snapshot-room",
        room_code="SNAPSHOT",
        status="RESOLVING",
        version=0,
        round_number=round_number,
        world=World(**world_data),
        max_rounds=max_rounds,
        initial_player_count=len(players),
        progress_points=_nonnegative_int(state["progress_points_before_round"]),
        danger_points=_nonnegative_int(state["danger_points_before_round"]),
        players=players,
        entries=entries,
        dice_results=dice_results,
    )


def _required_text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("snapshot text is required")
    return value


def _positive_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("snapshot integer must be positive")
    return value


def _nonnegative_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("snapshot integer must not be negative")
    return value
