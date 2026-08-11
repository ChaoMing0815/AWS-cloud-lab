from __future__ import annotations

from copy import deepcopy
from collections.abc import Callable
from threading import RLock
from typing import Any

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

    def get_by_code(self, room_code: str) -> Room | None:
        with self._lock:
            room = next(
                (item for item in self._rooms.values() if item.room_code == room_code),
                None,
            )
            return deepcopy(room) if room else None

    def save(self, room: Room) -> None:
        with self._lock:
            self._rooms[room.id] = deepcopy(room)

    def mutate(self, room_id: str, operation: Callable[[Room | None], Any]) -> Any:
        with self._lock:
            room = deepcopy(self._rooms[room_id]) if room_id in self._rooms else None
            result = operation(room)
            if room is not None:
                self._rooms[room.id] = deepcopy(room)
            return deepcopy(result)
