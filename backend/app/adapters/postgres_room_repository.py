from dataclasses import asdict

import psycopg
from psycopg.types.json import Jsonb

from app.application.ports import RoomRepository
from app.domain.models import Character, DiceResult, Player, Room, StoryEntry, World


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
                (room.id, room.room_code, room.status, room.version, Jsonb(asdict(room))),
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
        players.append(
            Player(
                **player,
                character=Character(**raw_character) if raw_character else None,
            )
        )
    entries = [StoryEntry(**entry) for entry in payload.pop("entries")]
    dice_results = [DiceResult(**result) for result in payload.pop("dice_results")]
    return Room(
        **payload,
        world=world,
        players=players,
        entries=entries,
        dice_results=dice_results,
    )
