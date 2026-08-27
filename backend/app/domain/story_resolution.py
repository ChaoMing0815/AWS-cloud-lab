from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from app.domain.models import Room
from app.domain.story_jobs import StoryJob


class StoryResolutionError(Exception):
    """Base error for replay-safe story resolution."""


class StoryResolutionConflict(StoryResolutionError):
    pass


class StoryResolutionOwnershipConflict(StoryResolutionConflict):
    pass


class StoryResolutionStateConflict(StoryResolutionConflict):
    pass


class StoryResolutionOutcome(str, Enum):
    APPLIED = "applied"
    STALE = "stale"
    FAILED = "failed"


@dataclass(frozen=True)
class StoryResolutionReceipt:
    job_id: str
    room_id: str
    round_number: int
    room_version: int
    result_fingerprint: str
    result: dict[str, Any]
    outcome: StoryResolutionOutcome
    room_version_after: int | None

    @classmethod
    def create(
        cls,
        *,
        job: StoryJob,
        outcome: StoryResolutionOutcome,
        result: dict[str, Any],
        room_version_after: int | None,
    ) -> "StoryResolutionReceipt":
        owned_result = deepcopy(result)
        return cls(
            job_id=job.job_id,
            room_id=job.room_id,
            round_number=job.round_number,
            room_version=job.room_version,
            result_fingerprint=story_result_fingerprint(owned_result),
            result=owned_result,
            outcome=outcome,
            room_version_after=room_version_after,
        )

    @property
    def completion_result(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "result_fingerprint": self.result_fingerprint,
        }


def story_result_fingerprint(result: dict[str, Any]) -> str:
    try:
        canonical = json.dumps(
            result,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as error:
        raise ValueError("story result must be JSON-compatible") from error
    return sha256(canonical.encode("utf-8")).hexdigest()


def build_story_resolution_snapshot(
    room: Room,
    *,
    source_room_version: int,
    skip_pending_spark: bool,
) -> dict[str, Any]:
    results = [
        result
        for result in room.dice_results
        if result.round_number == room.round_number
    ]
    players_by_id = {player.id: player for player in room.players}
    public_entries = [entry for entry in room.entries if entry.type != "action"][-5:]
    snapshot = {
        "operation": "resolve-round",
        "producer": {
            "source_room_version": source_room_version,
            "skip_pending_spark": skip_pending_spark,
        },
        "world": {
            "name": room.world.name,
            "story_title": room.world.story_title,
            "premise": room.world.premise,
            "objective": room.world.objective,
            "opening_scene": room.world.opening_scene,
            "core_obstacle": room.world.core_obstacle,
            "tone": room.world.tone,
            "custom_tone": room.world.custom_tone,
        },
        "canonical_state": {
            "round_number": room.round_number,
            "max_rounds": room.max_rounds,
            "progress_points_before_round": room.progress_points,
            "danger_points_before_round": room.danger_points,
            "progress_delta": sum(result.progress_delta for result in results),
            "danger_delta": sum(result.danger_delta for result in results),
        },
        "recent_story": [
            {
                "type": entry.type,
                "title": entry.title,
                "round_number": entry.round_number,
                "text": entry.text,
            }
            for entry in public_entries
        ],
        "resolved_actions": [
            _resolved_action(players_by_id[result.player_id], result)
            for result in results
            if result.player_id in players_by_id
        ],
    }
    return deepcopy(snapshot)


def _resolved_action(player, result) -> dict[str, Any]:
    character = player.character
    return {
        "player_id": player.id,
        "player_name": player.name,
        "role": player.role,
        "action": player.action,
        "approach": player.action_approach,
        "character": (
            {
                "name": character.name,
                "background": character.background,
                "trait": character.trait,
                "weakness": character.weakness,
                "courage": character.courage,
                "insight": character.insight,
                "bond": character.bond,
                "spark": character.spark,
            }
            if character is not None
            else None
        ),
        "dice": {
            "d6_1": result.d6_1,
            "d6_2": result.d6_2,
            "attribute_value": result.attribute_value,
            "base_total": result.base_total,
            "final_total": result.final_total,
            "result": result.result,
            "progress_delta": result.progress_delta,
            "danger_delta": result.danger_delta,
            "spark_used": result.spark_used,
            "spark_decision": result.spark_decision,
        },
    }
