from app.application.rules import points_percent, target_points
from app.domain.models import Room


def room_response(room: Room, session: dict) -> dict:
    current_player_id = session.get("playerId")
    target = target_points(room.initial_player_count, room.max_rounds)
    latest_dice_round = max(
        (result.round_number for result in room.dice_results),
        default=room.round_number,
    )
    return {
        "id": room.id,
        "roomCode": room.room_code,
        "status": room.status,
        "version": room.version,
        "worldGenerationCount": room.world_generation_count,
        "round": room.round_number,
        "world": {
            "name": room.world.name,
            "storyTitle": room.world.story_title,
            "premise": room.world.premise,
            "objective": room.world.objective,
            "openingScene": room.world.opening_scene,
            "coreObstacle": room.world.core_obstacle,
            "tone": room.world.tone,
            "customTone": room.world.custom_tone,
        },
        "maxRounds": room.max_rounds,
        "initialPlayerCount": room.initial_player_count,
        "players": [
            {
                "id": player.id,
                "name": player.name,
                "role": player.role,
                "action": player.action if player.id == current_player_id else "",
                "actionApproach": player.action_approach if player.id == current_player_id else "",
                "hasSubmitted": bool(player.action),
                "characterReady": player.character is not None,
                "character": (
                    {
                        "name": player.character.name,
                        "background": player.character.background,
                        "trait": player.character.trait,
                        "weakness": player.character.weakness,
                        "courage": player.character.courage,
                        "insight": player.character.insight,
                        "bond": player.character.bond,
                        "spark": player.character.spark,
                    }
                    if player.character
                    else None
                ),
            }
            for player in room.players
        ],
        "entries": [
            {
                "id": entry.id,
                "type": entry.type,
                "title": entry.title,
                "round": entry.round_number,
                "text": entry.text,
            }
            for entry in room.entries
            if (
                entry.type != "action"
                or entry.round_number < room.round_number
                or room.status
                in {"AWAITING_SPARK", "RESOLVING", "COMPLETION_AVAILABLE", "COMPLETED"}
            )
        ],
        "progressPoints": room.progress_points,
        "dangerPoints": room.danger_points,
        "targetPoints": target,
        "progressPercent": points_percent(room.progress_points, target),
        "dangerPercent": points_percent(room.danger_points, target),
        "endingResult": room.ending_result,
        "endingCost": room.ending_cost,
        "successLocked": room.success_locked,
        "resolutionMode": room.resolution_mode,
        "resolutionFailureCode": room.resolution_failure_code,
        "resolutionAttempts": room.resolution_attempts,
        "pendingProgress": sum(
            result.progress_delta
            for result in room.dice_results
            if result.round_number == room.round_number
            and room.status in {"AWAITING_SPARK", "RESOLVING"}
        ),
        "pendingDanger": sum(
            result.danger_delta
            for result in room.dice_results
            if result.round_number == room.round_number
            and room.status in {"AWAITING_SPARK", "RESOLVING"}
        ),
        "diceResults": [
            {
                "playerId": result.player_id,
                "round": result.round_number,
                "dice": [result.d6_1, result.d6_2],
                "approach": result.approach,
                "attributeValue": result.attribute_value,
                "baseTotal": result.base_total,
                "finalTotal": result.final_total,
                "result": result.result,
                "progressDelta": result.progress_delta,
                "dangerDelta": result.danger_delta,
                "sparkUsed": result.spark_used,
                "sparkDecision": result.spark_decision,
            }
            for result in room.dice_results
            if result.round_number == latest_dice_round
        ],
        "session": session,
    }
