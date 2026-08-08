from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class World:
    name: str
    story_title: str
    premise: str
    objective: str


@dataclass(slots=True)
class Player:
    id: str
    name: str
    role: str
    action: str = ""
    session_hash: str = ""
    csrf_token: str = ""


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
    players: list[Player] = field(default_factory=list)
    entries: list[StoryEntry] = field(default_factory=list)
