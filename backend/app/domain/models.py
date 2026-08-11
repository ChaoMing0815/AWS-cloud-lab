from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class World:
    name: str
    story_title: str
    premise: str
    objective: str
    opening_scene: str = ""
    core_obstacle: str = ""
    tone: str = "light_comedy"
    custom_tone: str | None = None


@dataclass(slots=True)
class Character:
    name: str
    background: str
    trait: str
    weakness: str
    courage: int
    insight: int
    bond: int
    spark: int = 1


@dataclass(slots=True)
class Player:
    id: str
    name: str
    role: str
    action: str = ""
    action_approach: str = ""
    session_hash: str = ""
    csrf_token: str = ""
    session_expires_at: datetime | None = None
    character: Character | None = None


@dataclass(slots=True)
class StoryEntry:
    id: str
    type: str
    title: str
    round_number: int
    text: str
    player_id: str | None = None


@dataclass(slots=True)
class DiceResult:
    player_id: str
    round_number: int
    d6_1: int
    d6_2: int
    approach: str
    attribute_value: int
    base_total: int
    final_total: int
    result: str
    progress_delta: int
    danger_delta: int
    spark_used: int = 0
    spark_decision: str = "PENDING"


@dataclass(slots=True)
class Room:
    id: str
    room_code: str
    status: str
    version: int
    round_number: int
    world: World
    host_session_hash: str = ""
    host_csrf_token: str = ""
    expires_at: datetime | None = None
    host_session_expires_at: datetime | None = None
    max_rounds: int = 6
    initial_player_count: int = 0
    progress_points: int = 0
    danger_points: int = 0
    ending_result: str | None = None
    ending_cost: str | None = None
    success_locked: bool = False
    resolution_mode: str | None = None
    resolution_failure_code: str | None = None
    resolution_attempts: int = 0
    players: list[Player] = field(default_factory=list)
    entries: list[StoryEntry] = field(default_factory=list)
    dice_results: list[DiceResult] = field(default_factory=list)
