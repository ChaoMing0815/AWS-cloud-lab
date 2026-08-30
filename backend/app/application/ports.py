from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.domain.models import Room
from app.domain.story_jobs import StoryJob
from app.domain.story_resolution import StoryResolutionReceipt


RETRYABLE_STORYTELLER_FAILURES = {
    "TIMEOUT",
    "THROTTLED",
    "TRANSIENT_SERVICE_ERROR",
    "SCHEMA_INVALID",
}

STORYTELLER_SCHEMA_DIAGNOSTIC_CODES = {
    "unexpected_stop_reason",
    "unexpected_content_count",
    "unexpected_content_block",
    "unexpected_tool_shape",
    "unexpected_tool_use_id",
    "unexpected_tool_name",
    "round_input_keys",
    "round_player_consequence_count",
    "round_player_consequence_shape",
    "round_player_id_bounds",
    "round_action_consequence_bounds",
    "round_player_set",
    "round_narrative_bounds",
    "round_progress_consequence_bounds",
    "round_crisis_consequence_bounds",
    "round_next_scene_hook_bounds",
}


class StorytellerFailure(Exception):
    def __init__(self, code: str, *, diagnostic_code: str | None = None) -> None:
        if diagnostic_code is not None and (
            code != "SCHEMA_INVALID"
            or diagnostic_code not in STORYTELLER_SCHEMA_DIAGNOSTIC_CODES
        ):
            raise ValueError("diagnostic_code")
        super().__init__(code)
        self.code = code
        self.diagnostic_code = diagnostic_code

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
        ownership_token: str,
        result: dict[str, Any],
    ) -> StoryJob: ...

    @abstractmethod
    def fail(
        self,
        job_id: str,
        ownership_token: str,
        error_code: str,
    ) -> StoryJob: ...


class StoryResolutionStore(ABC):
    @abstractmethod
    def begin_resolution(
        self,
        room_id: str,
        round_number: int,
        expected_version: int,
        skip_pending_spark: bool,
    ) -> StoryJob: ...

    @abstractmethod
    def result_for_claim(self, job: StoryJob) -> StoryResolutionReceipt | None: ...

    @abstractmethod
    def commit_result(
        self,
        job: StoryJob,
        result: dict[str, Any],
    ) -> StoryResolutionReceipt: ...

    @abstractmethod
    def mark_completion_dispatched(
        self,
        job_id: str,
        ownership_token: str,
    ) -> None: ...


class StoryResolutionNarrator(ABC):
    @abstractmethod
    def resolve(self, snapshot: dict[str, Any]) -> dict[str, Any]: ...


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
