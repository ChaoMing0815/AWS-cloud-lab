from __future__ import annotations

from dataclasses import dataclass, field


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
    session_hash: str = ""
    csrf_token: str = ""
    character: Character | None = None


@dataclass(slots=True)
class StoryEntry:
    id: str
    type: str
    title: str
    round_number: int
    text: str


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
    max_rounds: int = 6
    initial_player_count: int = 0
    players: list[Player] = field(default_factory=list)
    entries: list[StoryEntry] = field(default_factory=list)
