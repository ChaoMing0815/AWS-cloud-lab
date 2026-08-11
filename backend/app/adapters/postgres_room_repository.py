from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import psycopg
from psycopg.types.json import Jsonb

from app.application.ports import RoomRepository
from app.domain.models import Character, DiceResult, Player, Room, StoryEntry, World


def _room_payload(room: Room) -> dict:
    payload = asdict(room)
    payload["expires_at"] = _datetime_to_json(room.expires_at)
    payload["host_session_expires_at"] = _datetime_to_json(
        room.host_session_expires_at
    )
    for player_payload, player in zip(payload["players"], room.players, strict=True):
        player_payload["session_expires_at"] = _datetime_to_json(
            player.session_expires_at
        )
    return payload


def _datetime_to_json(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("lifecycle datetime must be UTC-aware")
    return value.isoformat()


def _datetime_from_json(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value) if isinstance(value, str) else value
    if parsed.tzinfo is None:
        raise ValueError("stored lifecycle datetime must be timezone-aware")
    return parsed.astimezone(timezone.utc)


class PostgresRoomRepository(RoomRepository):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def get(self, room_id: str) -> Room | None:
        return self._find("id", room_id)

    def get_by_code(self, room_code: str) -> Room | None:
        return self._find("room_code", room_code)

    def save(self, room: Room) -> None:
        with psycopg.connect(self.dsn) as connection:
            connection.execute(
                """
                INSERT INTO rooms (id, room_code, status, version, payload)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    room_code = EXCLUDED.room_code,
                    status = EXCLUDED.status,
                    version = EXCLUDED.version,
                    payload = EXCLUDED.payload,
                    updated_at = now()
                """,
                (room.id, room.room_code, room.status, room.version, Jsonb(_room_payload(room))),
            )

    def _find(self, field: str, value: str) -> Room | None:
        if field not in {"id", "room_code"}:
            raise ValueError("unsupported room lookup")
        with psycopg.connect(self.dsn) as connection:
            row = connection.execute(
                f"SELECT payload FROM rooms WHERE {field} = %s",
                (value,),
            ).fetchone()
        return _room_from_payload(row[0]) if row else None


def _room_from_payload(data: dict) -> Room:
    payload = dict(data)
    world = World(**payload.pop("world"))
    players = []
    for raw_player in payload.pop("players"):
        player = dict(raw_player)
        raw_character = player.pop("character")
        player["session_expires_at"] = _datetime_from_json(
            player.get("session_expires_at")
        )
        players.append(
            Player(
                **player,
                character=Character(**raw_character) if raw_character else None,
            )
        )
    entries = [StoryEntry(**entry) for entry in payload.pop("entries")]
    dice_results = [DiceResult(**result) for result in payload.pop("dice_results")]
    payload["expires_at"] = _datetime_from_json(payload.get("expires_at"))
    payload["host_session_expires_at"] = _datetime_from_json(
        payload.get("host_session_expires_at")
    )
    return Room(
        **payload,
        world=world,
        players=players,
        entries=entries,
        dice_results=dice_results,
    )
