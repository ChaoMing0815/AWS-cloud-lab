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
        },
        "players": [
            {
                "id": player.id,
                "name": player.name,
                "role": player.role,
                "action": player.action if player.id == current_player_id else "",
                "hasSubmitted": bool(player.action),
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
            if entry.type != "action" or entry.round_number < room.round_number
        ],
        "session": session,
    }
