from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.domain.models import Room


RETRYABLE_STORYTELLER_FAILURES = {
    "TIMEOUT",
    "THROTTLED",
    "TRANSIENT_SERVICE_ERROR",
    "SCHEMA_INVALID",
}


class StorytellerFailure(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code

    @property
    def retryable(self) -> bool:
        return self.code in RETRYABLE_STORYTELLER_FAILURES


class RoomRepository(ABC):
    @abstractmethod
    def get(self, room_id: str) -> Room | None: ...

    @abstractmethod
    def get_by_code(self, room_code: str) -> Room | None: ...

    @abstractmethod
    def save(self, room: Room) -> None: ...


class Storyteller(ABC):
    @abstractmethod
    def resolve_round(self, room: Room) -> str: ...

    @abstractmethod
    def resolve_ending(self, room: Room) -> str: ...


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


class DiceRoller(ABC):
    @abstractmethod
    def roll_d6(self) -> int: ...


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime: ...
