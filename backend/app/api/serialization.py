from app.domain.models import Room


def room_response(room: Room, session: dict) -> dict:
    current_player_id = session.get("playerId")
    return {
        "id": room.id,
        "roomCode": room.room_code,
        "status": room.status,
        "version": room.version,
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
                or room.status == "AWAITING_SPARK"
            )
        ],
        "progressPoints": room.progress_points,
        "dangerPoints": room.danger_points,
        "pendingProgress": sum(
            result.progress_delta
            for result in room.dice_results
            if result.round_number == room.round_number
        ),
        "pendingDanger": sum(
            result.danger_delta
            for result in room.dice_results
            if result.round_number == room.round_number
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
            }
            for result in room.dice_results
            if result.round_number == room.round_number
        ],
        "session": session,
    }
