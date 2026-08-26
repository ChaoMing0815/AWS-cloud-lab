from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.domain.models import Room
from app.domain.story_jobs import StoryJob


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

    @abstractmethod
    def mutate(self, room_id: str, operation: Callable[[Room | None], Any]) -> Any: ...

    @abstractmethod
    def delete(self, room_id: str, operation: Callable[[Room | None], Any]) -> Any: ...

    @abstractmethod
    def delete_expired_at_or_before(self, now: datetime) -> int: ...


class Storyteller(ABC):
    @abstractmethod
    def generate_world(
        self,
        keywords: list[str],
        tone: str,
        custom_tone: str | None,
        supplemental_request: str | None,
    ) -> "World": ...

    @abstractmethod
    def resolve_round(self, room: Room) -> str: ...

    @abstractmethod
    def resolve_ending(self, room: Room) -> str: ...


class StoryJobQueue(ABC):
    @abstractmethod
    def enqueue(self, job: StoryJob) -> StoryJob: ...

    @abstractmethod
    def claim(self, job_id: str, worker_id: str) -> StoryJob: ...

    @abstractmethod
    def complete(
        self,
        job_id: str,
        worker_id: str,
        result: dict[str, Any],
    ) -> StoryJob: ...


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
