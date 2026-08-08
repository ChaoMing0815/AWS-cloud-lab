from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from app.domain.models import Room


class RoomRepository(ABC):
    @abstractmethod
    def get(self, room_id: str) -> Room | None: ...

    @abstractmethod
    def save(self, room: Room) -> None: ...


class Storyteller(ABC):
    @abstractmethod
    def resolve_round(self, room: Room) -> str: ...


class IdempotencyStore(ABC):
    @abstractmethod
    def execute(
        self,
        scope: str,
        key: str,
        payload: dict[str, Any],
        operation: Callable[[], Any],
    ) -> Any: ...


class SessionTokenFactory(ABC):
    @abstractmethod
    def derive(self, purpose: str, idempotency_key: str) -> str: ...
