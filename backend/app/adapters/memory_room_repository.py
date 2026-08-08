from __future__ import annotations

from copy import deepcopy
from threading import RLock

from app.application.ports import RoomRepository
from app.domain.models import Room


class MemoryRoomRepository(RoomRepository):
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._lock = RLock()

    def get(self, room_id: str) -> Room | None:
        with self._lock:
            room = self._rooms.get(room_id)
            return deepcopy(room) if room else None

    def save(self, room: Room) -> None:
        with self._lock:
            self._rooms[room.id] = deepcopy(room)
