from __future__ import annotations

import hmac
import json
import logging
import secrets
import string
from datetime import datetime, timedelta
from uuid import uuid4

from app.application.ports import (
    Clock,
    DiceRoller,
    IdempotencyStore,
    RoomRepository,
    SessionTokenFactory,
    Storyteller,
    StorytellerFailure,
)
from app.application.input_safety import contains_explicit_prompt_injection
from app.application.rules import (
    apply_spark,
    classify_result,
    ending_cost,
    ending_result,
    points_percent,
    target_points,
)
from app.application.security import hash_session_token
from app.application.session_lifecycle import is_expired_at
from app.domain.errors import DomainError
from app.domain.models import Character, DiceResult, Player, Room, StoryEntry, TransferCode, World

ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
STORYTELLER_LOGGER = logging.getLogger("co_story.storyteller")
STORYTELLER_RECOVERY_LOGGER = logging.getLogger("co_story.storyteller_recovery")
STORYTELLER_FAILURE_CODES = {
    "AUTHORIZATION_ERROR",
    "CONTENT_REJECTED",
    "INVALID_MODEL",
    "SCHEMA_INVALID",
    "THROTTLED",
    "TIMEOUT",
    "TRANSIENT_SERVICE_ERROR",
}
TRANSFER_CODE_ISSUE_STATUSES = {
    "DRAFT",
    "LOBBY",
    "COLLECTING_ACTIONS",
    "AWAITING_HOST",
    "AWAITING_SPARK",
    "RESOLVING",
    "RESOLUTION_FAILED",
    "COMPLETION_AVAILABLE",
    "COMPLETED",
}


def _new_id() -> str:
    return str(uuid4())


def _room_code() -> str:
    return "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(6))


def _default_world() -> World:
    return World(
        name="年終尾牙作戰",
        story_title="尾牙前的最後一份提案",
        premise="公司臨時宣布加碼大獎，但抽獎資格取決於各部門能否完成最後一項共同任務。",
        objective="在尾牙抽獎前完成跨部門提案，爭取加碼年終獎金。",
        opening_scene="尾牙開始前一小時，跨部門提案的關鍵數據仍散落在三個互不相讓的部門手中。",
        core_obstacle="最新版預算表被印成抽獎箱封條，活動組拒絕在開場前重新製作。",
        tone="workplace_satire",
    )


def _empty_world() -> World:
    return World(name="尚未命名", story_title="尚未命名", premise="", objective="")


class RoomService:
    def __init__(
        self,
        repository: RoomRepository,
        storyteller: Storyteller,
        idempotency: IdempotencyStore,
        token_factory: SessionTokenFactory,
        dice_roller: DiceRoller,
        clock: Clock,
        *,
        seed_demo_room: bool = True,
    ) -> None:
        self.repository = repository
        self.storyteller = storyteller
        self.idempotency = idempotency
        self.token_factory = token_factory
        self.dice_roller = dice_roller
        self.clock = clock
        self.demo_room_id = self._create_demo_room() if seed_demo_room else None

    def _create_demo_room(self) -> str:
        existing = self.repository.get_by_code("BONUS7")
        if existing is not None:
            return existing.id
        room = Room(
            id=_new_id(),
            room_code="BONUS7",
            status="COLLECTING_ACTIONS",
            version=1,
            round_number=4,
            world=_default_world(),
            players=[
                Player(id=_new_id(), name="昭銘", role="總務部的新鮮人"),
                Player(id=_new_id(), name="凜", role="冷靜的工程師"),
                Player(id=_new_id(), name="洛河", role="人脈廣的企劃"),
            ],
            entries=[
                StoryEntry(
                    id=_new_id(),
                    type="narrator",
                    title="故事主持人",
                    round_number=3,
                    text="尾牙開始前一小時，關鍵數據仍散落在三個互不相讓的部門手中。",
                ),
                StoryEntry(
                    id=_new_id(),
                    type="narrator",
                    title="故事主持人",
                    round_number=4,
                    text="最新版預算表被印成尾牙抽獎箱的封條。你們必須說服活動組重新製作封條。",
                ),
            ],
        )
        self.repository.save(room)
        return room.id

    def load_current(self, room_id: str | None) -> Room:
        if room_id:
            room = self.repository.get(room_id)
            if room:
                return room
        if self.demo_room_id is None:
            raise DomainError("ROOM_NOT_FOUND", "找不到目前房間。", 404)
        room = self.repository.get(self.demo_room_id)
        if room is None:
            raise RuntimeError("Demo room was not initialized")
        return room

    def current_session_summary(
        self,
        room_id: str | None,
        host_token: str | None,
        player_token: str | None,
    ) -> dict:
        if not room_id:
            return {
                "authenticated": False,
                "principalType": "anonymous",
                "isHost": False,
                "room": None,
                "continueRoute": None,
            }

        room = self.repository.get(room_id)
        if room is None:
            raise DomainError("SESSION_NOT_FOUND", "目前的遊戲工作階段已失效。", 401)
        session = self.session_context(room, host_token, player_token)
        if session["principalType"] == "anonymous":
            raise DomainError("SESSION_NOT_FOUND", "目前的遊戲工作階段已失效。", 401)

        if room.status == "DRAFT":
            if not session["isHost"]:
                raise DomainError("SESSION_NOT_FOUND", "目前的遊戲工作階段已失效。", 401)
            continue_route = "/host/setup"
        elif room.status == "LOBBY":
            continue_route = f"/room/{room.room_code}/lobby"
        elif room.status == "COMPLETED":
            continue_route = f"/room/{room.room_code}/ending"
        else:
            continue_route = f"/room/{room.room_code}/play"

        return {
            "authenticated": True,
            "principalType": session["principalType"],
            "isHost": session["isHost"],
            "room": {
                "id": room.id,
                "roomCode": room.room_code,
                "status": room.status,
            },
            "continueRoute": continue_route,
        }

    def create_room(self, nickname: str, idempotency_key: str) -> tuple[Room, str, str]:
        name = nickname.strip()
        if not 1 <= len(name) <= 12 or any(
            char in string.whitespace and char not in " " for char in name
        ):
            raise DomainError("INVALID_NICKNAME", "暱稱必須是 1–12 個可見字元。", 422)
        host_token = self.token_factory.derive("host-session", idempotency_key)
        host_csrf = self.token_factory.derive("host-csrf", idempotency_key)
        player_token = self.token_factory.derive("host-player-session", idempotency_key)
        player_csrf = self.token_factory.derive("host-player-csrf", idempotency_key)
        expires_at = self.clock.now() + timedelta(days=7)

        def operation() -> Room:
            creator = Player(
                id=_new_id(),
                name=name,
                role="共同創作者",
                session_hash=hash_session_token(player_token),
                csrf_token=player_csrf,
                session_expires_at=expires_at,
            )
            room = Room(
                id=_new_id(),
                room_code=_room_code(),
                status="DRAFT",
                version=1,
                round_number=1,
                world=_empty_world(),
                host_session_hash=hash_session_token(host_token),
                host_csrf_token=host_csrf,
                host_player_id=creator.id,
                expires_at=expires_at,
                host_session_expires_at=expires_at,
                players=[creator],
                entries=[
                    StoryEntry(
                        id=_new_id(),
                        type="narrator",
                        title="故事主持人",
                        round_number=1,
                        text="新房間已建立。請房主先完成並確認世界設定。",
                    )
                ],
            )
            self.repository.save(room)
            return room

        room = self.idempotency.execute(
            "create-room",
            idempotency_key,
            {"nickname": name},
            operation,
        )
        return room, host_token, player_token

    def confirm_world(
        self,
        room_id: str,
        world_data: dict,
        max_rounds: int,
        expected_version: int,
        host_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> Room:
        room = self._required_room(room_id)
        self._authorize_host(room, host_token, csrf_token)

        def operation() -> Room:
            current = self._required_room(room_id)
            self._check_version(current, expected_version)
            if current.status != "DRAFT":
                raise DomainError("WORLD_ALREADY_CONFIRMED", "世界設定已確認。", 409)
            title = world_data["story_title"].strip()
            current.world = World(
                name=title,
                story_title=title,
                premise=world_data["premise"].strip(),
                objective=world_data["objective"].strip(),
                opening_scene=world_data["opening_scene"].strip(),
                core_obstacle=world_data["core_obstacle"].strip(),
                tone=world_data["tone"],
                custom_tone=(world_data.get("custom_tone") or "").strip() or None,
            )
            current.max_rounds = max_rounds
            current.status = "LOBBY"
            current.version += 1
            current.entries.append(
                StoryEntry(
                    id=_new_id(),
                    type="narrator",
                    title="故事主持人",
                    round_number=1,
                    text="世界設定已確認。邀請 3–5 位玩家加入後，由房主開始遊戲。",
                )
            )
            self._refresh_activity(current, host=True)
            self.repository.save(current)
            return current

        payload = {**world_data, "max_rounds": max_rounds, "room_version": expected_version}
        return self.idempotency.execute(
            f"confirm-world:{room_id}", idempotency_key, payload, operation
        )

    def generate_world(
        self,
        room_id: str,
        keywords: list[str],
        tone: str,
        custom_tone: str | None,
        supplemental_request: str | None,
        expected_version: int,
        host_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> Room:
        room = self._required_room(room_id)
        self._authorize_host(room, host_token, csrf_token)

        def operation() -> dict:
            current = self._required_room(room_id)
            self._check_version(current, expected_version)
            if current.status != "DRAFT":
                raise DomainError("WORLD_ALREADY_CONFIRMED", "世界設定已確認。", 409)
            if current.world_generation_count >= 2:
                raise DomainError("WORLD_GENERATION_LIMIT", "世界生成次數已達上限。", 409)
            if contains_explicit_prompt_injection(
                *keywords,
                custom_tone,
                supplemental_request,
            ):
                raise DomainError(
                    "PROMPT_INJECTION_REJECTED",
                    "輸入包含疑似提示注入指令，請改寫故事要求。",
                    422,
                )

            current.world_generation_count += 1
            current.version += 1
            self.repository.save(current)
            try:
                generated = self.storyteller.generate_world(
                    keywords, tone, custom_tone, supplemental_request
                )
            except StorytellerFailure as failure:
                failure_code = (
                    failure.code
                    if failure.code in STORYTELLER_FAILURE_CODES
                    else "UNKNOWN"
                )
                STORYTELLER_LOGGER.warning(
                    json.dumps(
                        {
                            "operation": "generate_world",
                            "failure_code": failure_code,
                        },
                        separators=(",", ":"),
                    )
                )
                return {"room": current, "failure": failure.code}

            current.world = generated
            self.repository.save(current)
            return {"room": current, "failure": None}

        outcome = self.idempotency.execute(
            f"generate-world:{room_id}",
            idempotency_key,
            {
                "keywords": keywords,
                "tone": tone,
                "custom_tone": custom_tone,
                "supplemental_request": supplemental_request,
                "room_version": expected_version,
            },
            operation,
        )
        if outcome["failure"]:
            if outcome["failure"] == "CONTENT_REJECTED":
                raise DomainError("WORLD_GENERATION_REJECTED", "世界生成暫時無法完成。", 422)
            raise DomainError("WORLD_GENERATION_UNAVAILABLE", "世界生成暫時無法完成。", 503)
        return outcome["room"]

    def start_game(
        self,
        room_id: str,
        expected_version: int,
        host_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> Room:
        room = self._required_room(room_id)
        self._authorize_host(room, host_token, csrf_token)

        def operation() -> Room:
            current = self._required_room(room_id)
            self._check_version(current, expected_version)
            if current.status != "LOBBY":
                raise DomainError("ROOM_NOT_STARTABLE", "只有等待中的房間可以開始。", 409)
            if not 3 <= len(current.players) <= 5:
                raise DomainError("PLAYER_COUNT_INVALID", "需要 3–5 位玩家才能開始。", 409)
            if any(player.character is None for player in current.players):
                raise DomainError("CHARACTERS_INCOMPLETE", "所有玩家都必須先完成角色。", 409)
            current.status = "COLLECTING_ACTIONS"
            current.initial_player_count = len(current.players)
            current.version += 1
            current.entries.append(
                StoryEntry(
                    id=_new_id(),
                    type="narrator",
                    title="故事主持人",
                    round_number=1,
                    text=current.world.opening_scene,
                )
            )
            self._refresh_activity(current, host=True)
            self.repository.save(current)
            return current

        return self.idempotency.execute(
            f"start-game:{room_id}",
            idempotency_key,
            {"room_version": expected_version},
            operation,
        )

    def join_room(
        self,
        room_id: str,
        nickname: str,
        role: str,
        expected_version: int,
        idempotency_key: str,
    ) -> tuple[Room, str]:
        player_token = self.token_factory.derive(f"player-session:{room_id}", idempotency_key)
        player_csrf = self.token_factory.derive(f"player-csrf:{room_id}", idempotency_key)

        def operation() -> Room:
            room = self._required_room(room_id)
            self._check_version(room, expected_version)
            if room.status != "LOBBY":
                raise DomainError("ROOM_NOT_JOINABLE", "只有等待中的房間可以加入玩家。", 409)
            name = nickname.strip()
            role_text = role.strip()
            if not 1 <= len(name) <= 12 or any(
                char in string.whitespace and char not in " " for char in name
            ):
                raise DomainError("INVALID_NICKNAME", "暱稱必須是 1–12 個可見字元。", 422)
            if not 1 <= len(role_text) <= 20:
                raise DomainError("INVALID_ROLE", "角色概念必須是 1–20 個字元。", 422)
            if len(room.players) >= 5:
                raise DomainError("ROOM_FULL", "房間已達 5 人上限。", 409)
            if any(player.name.casefold() == name.casefold() for player in room.players):
                raise DomainError("NICKNAME_TAKEN", "這個暱稱已有人使用。", 409)
            room.players.append(
                Player(
                    id=_new_id(),
                    name=name,
                    role=role_text,
                    session_hash=hash_session_token(player_token),
                    csrf_token=player_csrf,
                )
            )
            room.version += 1
            self._refresh_activity(room, player_id=room.players[-1].id)
            self.repository.save(room)
            return room

        payload = {"nickname": nickname, "role": role, "room_version": expected_version}
        room = self.idempotency.execute(f"join-room:{room_id}", idempotency_key, payload, operation)
        return room, player_token

    def join_room_by_code(
        self,
        room_code: str,
        nickname: str,
        idempotency_key: str,
    ) -> tuple[Room, str]:
        code = room_code.strip().upper()
        if len(code) != 6 or any(character not in ROOM_CODE_ALPHABET for character in code):
            raise DomainError("ROOM_CODE_INVALID", "房間代碼必須是六碼英數字。", 422)
        name = nickname.strip()
        if not 1 <= len(name) <= 12 or any(
            char in string.whitespace and char not in " " for char in name
        ):
            raise DomainError("INVALID_NICKNAME", "暱稱必須是 1–12 個可見字元。", 422)

        player_token = self.token_factory.derive(f"player-session:{code}", idempotency_key)
        player_csrf = self.token_factory.derive(f"player-csrf:{code}", idempotency_key)

        def operation() -> Room:
            room = self.repository.get_by_code(code)
            if room is None:
                raise DomainError("ROOM_NOT_FOUND", "找不到房間。", 404)
            if room.status != "LOBBY":
                raise DomainError("ROOM_NOT_JOINABLE", "只有等待中的房間可以加入玩家。", 409)
            if len(room.players) >= 5:
                raise DomainError("ROOM_FULL", "房間已達 5 人上限。", 409)
            if any(player.name.casefold() == name.casefold() for player in room.players):
                raise DomainError("NICKNAME_DUPLICATE", "這個暱稱已有人使用。", 409)
            room.players.append(
                Player(
                    id=_new_id(),
                    name=name,
                    role="共同創作者",
                    session_hash=hash_session_token(player_token),
                    csrf_token=player_csrf,
                )
            )
            room.version += 1
            self._refresh_activity(room, player_id=room.players[-1].id)
            self.repository.save(room)
            return room

        room = self.idempotency.execute(
            "join-room-by-code",
            idempotency_key,
            {"room_code": code, "nickname": name},
            operation,
        )
        return room, player_token

    def issue_transfer_code(
        self,
        room_id: str,
        player_id: str,
        expected_version: int,
        host_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> tuple[Room, str]:
        initial = self._required_room(room_id)
        self._authorize_host(initial, host_token, csrf_token)
        raw_code = self.token_factory.derive(
            f"transfer-code:{room_id}:{player_id}", idempotency_key
        )

        def operation() -> tuple[Room, str]:
            def issue(room: Room | None) -> tuple[Room, str]:
                if room is None:
                    raise DomainError("ROOM_NOT_FOUND", "找不到房間。", 404)
                self._authorize_host(room, host_token, csrf_token)
                self._check_version(room, expected_version)
                if room.status not in TRANSFER_CODE_ISSUE_STATUSES:
                    raise DomainError(
                        "TRANSFER_CODE_ISSUE_NOT_ALLOWED",
                        "目前不能發行角色轉移碼。",
                        409,
                    )
                player = next((item for item in room.players if item.id == player_id), None)
                if player is None:
                    raise DomainError("PLAYER_NOT_FOUND", "找不到指定玩家。", 404)
                now = self.clock.now()
                player.transfer_code = TransferCode(
                    code_hash=hash_session_token(raw_code),
                    issued_at=now,
                    expires_at=now + timedelta(minutes=10),
                )
                room.version += 1
                self._refresh_activity(room, host=True)
                return room, raw_code

            return self.repository.mutate(room_id, issue)

        return self.idempotency.execute(
            f"issue-transfer-code:{room_id}:{player_id}",
            idempotency_key,
            {"room_version": expected_version, "player_id": player_id},
            operation,
        )

    def redeem_transfer_code(
        self,
        room_id: str,
        player_id: str,
        transfer_code: str,
        expected_version: int,
        idempotency_key: str,
    ) -> tuple[Room, str, str]:
        player_token = self.token_factory.derive(
            f"reassigned-player-session:{room_id}:{player_id}", idempotency_key
        )
        player_csrf = self.token_factory.derive(
            f"reassigned-player-csrf:{room_id}:{player_id}", idempotency_key
        )

        def operation() -> tuple[Room, str, str]:
            def redeem(room: Room | None) -> tuple[Room, str, str]:
                now = self.clock.now()
                player = (
                    next((item for item in room.players if item.id == player_id), None)
                    if room is not None
                    else None
                )
                grant = player.transfer_code if player is not None else None
                if (
                    room is None
                    or not self._session_is_active(room.expires_at, now)
                    or room.status not in TRANSFER_CODE_ISSUE_STATUSES
                    or grant is None
                    or grant.consumed_at is not None
                    or is_expired_at(grant.expires_at, now)
                    or not hmac.compare_digest(
                        grant.code_hash, hash_session_token(transfer_code)
                    )
                ):
                    raise DomainError(
                        "TRANSFER_CODE_INVALID",
                        "角色轉移碼無效或已過期。",
                        401,
                    )
                self._check_version(room, expected_version)
                grant.consumed_at = now
                player.session_hash = hash_session_token(player_token)
                player.csrf_token = player_csrf
                player.session_expires_at = min(
                    now + timedelta(days=7), room.expires_at
                )
                room.version += 1
                return room, player_token, player_csrf

            return self.repository.mutate(room_id, redeem)

        return self.idempotency.execute(
            f"redeem-transfer-code:{room_id}:{player_id}",
            idempotency_key,
            {
                "transfer_code_hash": hash_session_token(transfer_code),
                "room_version": expected_version,
                "player_id": player_id,
            },
            operation,
        )

    def delete_room(
        self,
        room_id: str,
        expected_version: int,
        host_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> None:
        scope = f"delete-room:{room_id}"
        payload = {"room_version": expected_version}
        initial = self.repository.get(room_id)
        if initial is None:
            def missing_room() -> None:
                raise DomainError("ROOM_NOT_FOUND", "找不到房間。", 404)

            return self.idempotency.execute(scope, idempotency_key, payload, missing_room)
        self._authorize_host(initial, host_token, csrf_token)

        def operation() -> None:
            def delete(room: Room | None) -> None:
                if room is None:
                    raise DomainError("ROOM_NOT_FOUND", "找不到房間。", 404)
                self._authorize_host(room, host_token, csrf_token)
                self._check_version(room, expected_version)

            return self.repository.delete(room_id, delete)

        return self.idempotency.execute(scope, idempotency_key, payload, operation)

    def update_character(
        self,
        room_id: str,
        character_data: dict,
        expected_version: int,
        player_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> Room:
        room = self._required_room(room_id)
        player = self._authorize_player(room, player_token, csrf_token)

        def operation() -> Room:
            current = self._required_room(room_id)
            self._check_version(current, expected_version)
            if current.status != "LOBBY":
                raise DomainError("CHARACTER_NOT_EDITABLE", "只有等待中的房間可以編輯角色。", 409)
            attributes = (
                character_data["courage"],
                character_data["insight"],
                character_data["bond"],
            )
            if sum(attributes) != 3 or any(value < 0 or value > 2 for value in attributes):
                raise DomainError(
                    "INVALID_ATTRIBUTE_ALLOCATION",
                    "勇氣、洞察與羈絆各為 0–2，總和必須等於 3。",
                    422,
                )
            current_player = next(item for item in current.players if item.id == player.id)
            current_player.character = Character(
                name=character_data["name"].strip(),
                background=character_data["background"].strip(),
                trait=character_data["trait"].strip(),
                weakness=character_data["weakness"].strip(),
                courage=character_data["courage"],
                insight=character_data["insight"],
                bond=character_data["bond"],
                spark=1,
            )
            current.version += 1
            self.repository.save(current)
            return current

        payload = {**character_data, "room_version": expected_version, "player_id": player.id}
        return self.idempotency.execute(
            f"update-character:{room_id}:{player.id}",
            idempotency_key,
            payload,
            operation,
        )

    def submit_action(
        self,
        room_id: str,
        round_number: int,
        text: str,
        approach: str,
        expected_version: int,
        player_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> Room:
        room = self._required_room(room_id)
        player = self._authorize_player(room, player_token, csrf_token)

        def operation() -> Room:
            current = self._required_room(room_id)
            self._check_version(current, expected_version)
            if current.status not in {"COLLECTING_ACTIONS", "AWAITING_HOST"}:
                raise DomainError("ACTION_NOT_ALLOWED", "目前不能提交行動。", 409)
            if round_number != current.round_number:
                raise DomainError("ROUND_MISMATCH", "回合已更新，請重新載入。", 409)
            current_player = next(item for item in current.players if item.id == player.id)
            action = text.strip()
            if not 1 <= len(action) <= 240:
                raise DomainError("INVALID_ACTION", "行動必須是 1–240 個字元。", 422)

            if current_player.character is None:
                raise DomainError("CHARACTER_REQUIRED", "請先完成角色才能提交行動。", 409)
            if approach not in {"courage", "insight", "bond"}:
                raise DomainError("INVALID_APPROACH", "行動方式必須是勇氣、洞察或羈絆。", 422)

            current_player.action = action
            current_player.action_approach = approach
            current.entries = [
                entry
                for entry in current.entries
                if not (
                    entry.type == "action"
                    and entry.round_number == current.round_number
                    and entry.player_id == current_player.id
                )
            ]
            current.entries.append(
                StoryEntry(
                    id=_new_id(),
                    type="action",
                    title=f"{current_player.name} · {current_player.role}",
                    round_number=current.round_number,
                    text=action,
                    player_id=current_player.id,
                )
            )
            current.version += 1

            current.status = (
                "AWAITING_HOST"
                if len(current.players) >= 3 and all(item.action for item in current.players)
                else "COLLECTING_ACTIONS"
            )
            self._refresh_activity(current, player_id=current_player.id)
            self.repository.save(current)
            return current

        payload = {
            "round_number": round_number,
            "text": text,
            "approach": approach,
            "room_version": expected_version,
            "player_id": player.id,
        }
        return self.idempotency.execute(
            f"submit-action:{room_id}:{round_number}:{player.id}",
            idempotency_key,
            payload,
            operation,
        )

    def roll_round(
        self,
        room_id: str,
        round_number: int,
        expected_version: int,
        host_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> Room:
        room = self._required_room(room_id)
        self._authorize_host(room, host_token, csrf_token)

        def operation() -> Room:
            current = self._required_room(room_id)
            self._check_version(current, expected_version)
            if current.status != "AWAITING_HOST":
                raise DomainError("ROLL_NOT_ALLOWED", "尚未收齊行動，或本回合已擲骰。", 409)
            if round_number != current.round_number:
                raise DomainError("ROUND_MISMATCH", "回合已更新，請重新載入。", 409)

            current.dice_results = [
                result for result in current.dice_results if result.round_number != round_number
            ]
            for player in current.players:
                if not player.action or not player.action_approach or player.character is None:
                    raise DomainError("ACTIONS_INCOMPLETE", "必須收齊所有玩家行動才能擲骰。", 409)
                d6_1 = self.dice_roller.roll_d6()
                d6_2 = self.dice_roller.roll_d6()
                attribute_value = getattr(player.character, player.action_approach)
                total = d6_1 + d6_2 + attribute_value
                outcome = classify_result(total)
                current.dice_results.append(
                    DiceResult(
                        player_id=player.id,
                        round_number=round_number,
                        d6_1=d6_1,
                        d6_2=d6_2,
                        approach=player.action_approach,
                        attribute_value=attribute_value,
                        base_total=total,
                        final_total=total,
                        result=outcome.result,
                        progress_delta=outcome.progress_delta,
                        danger_delta=outcome.danger_delta,
                        spark_decision=("DECLINE" if player.character.spark == 0 else "PENDING"),
                    )
                )
            current.status = (
                "RESOLVING"
                if all(result.spark_decision != "PENDING" for result in current.dice_results)
                else "AWAITING_SPARK"
            )
            current.version += 1
            self._refresh_activity(current, host=True)
            self.repository.save(current)
            return current

        return self.idempotency.execute(
            f"roll-round:{room_id}:{round_number}",
            idempotency_key,
            {"round_number": round_number, "room_version": expected_version},
            operation,
        )

    def decide_spark(
        self,
        room_id: str,
        round_number: int,
        decision: str,
        expected_version: int,
        player_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> Room:
        room = self._required_room(room_id)
        player = self._authorize_player(room, player_token, csrf_token)

        def operation() -> Room:
            current = self._required_room(room_id)
            self._check_version(current, expected_version)
            if current.status != "AWAITING_SPARK":
                raise DomainError("SPARK_NOT_ALLOWED", "目前不能提交星火決策。", 409)
            if round_number != current.round_number:
                raise DomainError("ROUND_MISMATCH", "回合已更新，請重新載入。", 409)
            result = next(
                (
                    item
                    for item in current.dice_results
                    if item.round_number == round_number and item.player_id == player.id
                ),
                None,
            )
            if result is None:
                raise DomainError("DICE_RESULT_NOT_FOUND", "找不到本回合的骰點結果。", 404)
            if result.spark_decision != "PENDING":
                raise DomainError("SPARK_ALREADY_DECIDED", "本回合已完成星火決策。", 409)
            current_player = next(item for item in current.players if item.id == player.id)
            if current_player.character is None:
                raise DomainError("CHARACTER_REQUIRED", "找不到可使用星火的角色。", 409)
            if decision == "USE" and current_player.character.spark < 1:
                raise DomainError("SPARK_UNAVAILABLE", "角色目前沒有可用星火。", 409)

            result.spark_decision = decision
            result.spark_used = 1 if decision == "USE" else 0
            final_total, outcome = apply_spark(result.base_total, decision == "USE")
            result.final_total = final_total
            result.result = outcome.result
            result.progress_delta = outcome.progress_delta
            result.danger_delta = outcome.danger_delta
            current.version += 1
            if all(
                item.spark_decision != "PENDING"
                for item in current.dice_results
                if item.round_number == round_number
            ):
                current.status = "RESOLVING"
            self._refresh_activity(current, player_id=current_player.id)
            self.repository.save(current)
            return current

        return self.idempotency.execute(
            f"decide-spark:{room_id}:{round_number}:{player.id}",
            idempotency_key,
            {
                "round_number": round_number,
                "decision": decision,
                "room_version": expected_version,
                "player_id": player.id,
            },
            operation,
        )

    def resolve_round(
        self,
        room_id: str,
        round_number: int,
        skip_pending_spark: bool,
        expected_version: int,
        host_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> Room:
        room = self._required_room(room_id)
        self._authorize_host(room, host_token, csrf_token)

        def operation() -> Room:
            current = self._required_room(room_id)
            self._check_version(current, expected_version)
            if current.status not in {
                "AWAITING_SPARK",
                "RESOLVING",
                "RESOLUTION_FAILED",
            }:
                raise DomainError("RESOLVE_NOT_ALLOWED", "目前不能結算回合。", 409)
            if round_number != current.round_number:
                raise DomainError("ROUND_MISMATCH", "回合已更新，請重新載入。", 409)
            results = [
                result
                for result in current.dice_results
                if result.round_number == round_number
            ]
            pending = [result for result in results if result.spark_decision == "PENDING"]
            if pending and not skip_pending_spark:
                raise DomainError(
                    "SPARK_DECISIONS_PENDING",
                    "仍有玩家尚未完成星火決策。",
                    409,
                )
            for result in pending:
                result.spark_decision = "DECLINE"

            current.status = "RESOLVING"
            narration, attempts, failure_code = self._resolve_story(current)
            current.resolution_attempts = attempts
            current.resolution_failure_code = failure_code
            if failure_code is not None:
                current.resolution_mode = None
                current.status = "RESOLUTION_FAILED"
                current.version += 1
                self._refresh_activity(current, host=True)
                self.repository.save(current)
                return current

            current.resolution_mode = "storyteller"
            current.progress_points += sum(result.progress_delta for result in results)
            current.danger_points += sum(result.danger_delta for result in results)
            for result in results:
                player = next(item for item in current.players if item.id == result.player_id)
                if player.character is None:
                    raise DomainError("CHARACTER_REQUIRED", "找不到結算所需角色。", 409)
                player.character.spark -= result.spark_used
                if result.result == "FAILURE":
                    player.character.spark = min(3, player.character.spark + 1)

            current.entries.append(
                StoryEntry(
                    id=_new_id(),
                    type="narrator",
                    title="故事主持人",
                    round_number=round_number,
                    text=narration,
                )
            )
            for player in current.players:
                player.action = ""
                player.action_approach = ""
            completed_round = current.round_number
            target = target_points(current.initial_player_count, current.max_rounds)
            progress_percent = points_percent(current.progress_points, target)
            completed = completed_round >= current.max_rounds
            if completed:
                self._complete_game(current, target)
            else:
                current.round_number += 1
                current.status = (
                    "COMPLETION_AVAILABLE"
                    if progress_percent >= 100
                    else "COLLECTING_ACTIONS"
                )
            current.version += 1
            self._refresh_activity(current, host=True, completed=completed)
            self.repository.save(current)
            return current

        return self.idempotency.execute(
            f"resolve-round:{room_id}:{round_number}",
            idempotency_key,
            {
                "round_number": round_number,
                "skip_pending_spark": skip_pending_spark,
                "room_version": expected_version,
            },
            operation,
        )

    def _resolve_story(self, room: Room) -> tuple[str, int, str | None]:
        attempts = 0
        while attempts < 2:
            attempts += 1
            try:
                narration = self.storyteller.resolve_round(room)
                self._log_storyteller_recovery(attempts - 1, 0)
                return narration, attempts, None
            except StorytellerFailure as failure:
                if not failure.retryable or attempts == 2:
                    self._log_storyteller_recovery(attempts - 1, 0)
                    return "", attempts, failure.code
        raise RuntimeError("storyteller retry loop exited unexpectedly")

    @staticmethod
    def _log_storyteller_recovery(retry_count: int, fallback_count: int) -> None:
        STORYTELLER_RECOVERY_LOGGER.info(
            json.dumps(
                {
                    "metric_type": "storyteller_recovery",
                    "operation": "resolve_round_narrative",
                    "retry_count": retry_count,
                    "fallback_count": fallback_count,
                },
                separators=(",", ":"),
            )
        )

    def fallback_round(
        self,
        room_id: str,
        round_number: int,
        expected_version: int,
        host_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> Room:
        room = self._required_room(room_id)
        self._authorize_host(room, host_token, csrf_token)

        def operation() -> Room:
            current = self._required_room(room_id)
            self._check_version(current, expected_version)
            if current.status != "RESOLUTION_FAILED":
                raise DomainError("FALLBACK_NOT_ALLOWED", "目前不需要使用備援敘事。", 409)
            if current.round_number != round_number:
                raise DomainError("ROUND_MISMATCH", "回合已更新，請重新載入。", 409)
            results = [
                result
                for result in current.dice_results
                if result.round_number == round_number
            ]
            current.progress_points += sum(result.progress_delta for result in results)
            current.danger_points += sum(result.danger_delta for result in results)
            for result in results:
                player = next(item for item in current.players if item.id == result.player_id)
                if player.character is None:
                    raise DomainError("CHARACTER_REQUIRED", "找不到結算所需角色。", 409)
                player.character.spark -= result.spark_used
                if result.result == "FAILURE":
                    player.character.spark = min(3, player.character.spark + 1)
            labels = {
                "SUCCESS": "成功",
                "PARTIAL_SUCCESS": "部分成功",
                "FAILURE": "失敗",
            }
            outcomes = "、".join(
                f"{next(player.name for player in current.players if player.id == result.player_id)}為{labels[result.result]}"
                for result in results
            )
            current.entries.append(
                StoryEntry(
                    id=_new_id(),
                    type="narrator",
                    title="系統備援敘事",
                    round_number=round_number,
                    text=(
                        f"系統依固定判定完成本回合：{outcomes}。"
                        "此為 deterministic fallback，未使用 AI 故事生成。"
                    ),
                )
            )
            for player in current.players:
                player.action = ""
                player.action_approach = ""
            completed_round = current.round_number
            target = target_points(current.initial_player_count, current.max_rounds)
            progress_percent = points_percent(current.progress_points, target)
            completed = completed_round >= current.max_rounds
            if completed:
                self._complete_game(current, target)
            else:
                current.round_number += 1
                current.status = (
                    "COMPLETION_AVAILABLE"
                    if progress_percent >= 100
                    else "COLLECTING_ACTIONS"
                )
            current.resolution_mode = "fallback"
            self._log_storyteller_recovery(0, 1)
            current.version += 1
            self._refresh_activity(current, host=True, completed=completed)
            self.repository.save(current)
            return current

        return self.idempotency.execute(
            f"fallback-round:{room_id}:{round_number}",
            idempotency_key,
            {"round_number": round_number, "room_version": expected_version},
            operation,
        )

    def finish_game(
        self,
        room_id: str,
        decision: str,
        expected_version: int,
        host_token: str,
        csrf_token: str,
        idempotency_key: str,
    ) -> Room:
        room = self._required_room(room_id)
        self._authorize_host(room, host_token, csrf_token)

        def operation() -> Room:
            current = self._required_room(room_id)
            self._check_version(current, expected_version)
            if current.status != "COMPLETION_AVAILABLE":
                raise DomainError("FINISH_NOT_ALLOWED", "目前不能選擇結局。", 409)
            current.success_locked = True
            completed = decision != "CONTINUE"
            if not completed:
                current.status = "COLLECTING_ACTIONS"
            else:
                target = target_points(current.initial_player_count, current.max_rounds)
                self._complete_game(current, target)
            current.version += 1
            self._refresh_activity(current, host=True, completed=completed)
            self.repository.save(current)
            return current

        return self.idempotency.execute(
            f"finish-game:{room_id}",
            idempotency_key,
            {"decision": decision, "room_version": expected_version},
            operation,
        )

    def _complete_game(self, room: Room, target: int) -> None:
        room.ending_result = ending_result(points_percent(room.progress_points, target))
        room.ending_cost = ending_cost(points_percent(room.danger_points, target))
        room.status = "COMPLETED"
        room.entries.append(
            StoryEntry(
                id=_new_id(),
                type="ending",
                title="故事結局",
                round_number=room.round_number,
                text=self.storyteller.resolve_ending(room),
            )
        )

    def _refresh_activity(
        self,
        room: Room,
        *,
        host: bool = False,
        player_id: str | None = None,
        completed: bool = False,
    ) -> None:
        activity_expiry = self.clock.now() + timedelta(days=7)
        if completed or room.status != "COMPLETED":
            room.expires_at = activity_expiry
        if room.expires_at is None:
            raise RuntimeError("Formal room expiry is required for session activity")
        actor_expiry = min(activity_expiry, room.expires_at)
        if host:
            room.host_session_expires_at = actor_expiry
        if player_id is not None:
            player = next(item for item in room.players if item.id == player_id)
            player.session_expires_at = actor_expiry

    def session_context(
        self,
        room: Room,
        host_token: str | None,
        player_token: str | None,
    ) -> dict:
        now = self.clock.now()
        if not self._session_is_active(room.expires_at, now):
            return self._anonymous_session()
        is_host = bool(
            host_token
            and room.host_session_hash
            and self._session_is_active(room.host_session_expires_at, now)
            and hmac.compare_digest(room.host_session_hash, hash_session_token(host_token))
        )
        player = self._player_for_token(room, player_token)
        if player is not None and not self._session_is_active(
            player.session_expires_at, now
        ):
            player = None
        if player:
            return {
                "principalType": "player",
                "playerId": player.id,
                "csrfToken": player.csrf_token,
                "isHost": is_host,
                "hostCsrfToken": room.host_csrf_token if is_host else None,
            }
        if is_host:
            return {
                "principalType": "host",
                "playerId": None,
                "csrfToken": room.host_csrf_token,
                "isHost": True,
                "hostCsrfToken": room.host_csrf_token,
            }
        return self._anonymous_session()

    @staticmethod
    def _anonymous_session() -> dict:
        return {
            "principalType": "anonymous",
            "playerId": None,
            "csrfToken": None,
            "isHost": False,
            "hostCsrfToken": None,
        }

    def _authorize_host(self, room: Room, host_token: str, csrf_token: str) -> None:
        now = self.clock.now()
        if (
            not self._session_is_active(room.expires_at, now)
            or not self._session_is_active(room.host_session_expires_at, now)
            or not host_token
            or not room.host_session_hash
            or not hmac.compare_digest(
                room.host_session_hash, hash_session_token(host_token)
            )
        ):
            raise DomainError("HOST_SESSION_REQUIRED", "需要有效的房主工作階段。", 401)
        if not csrf_token or not hmac.compare_digest(room.host_csrf_token, csrf_token):
            raise DomainError("CSRF_FAILED", "CSRF 驗證失敗。", 403)

    def _authorize_player(self, room: Room, player_token: str, csrf_token: str) -> Player:
        now = self.clock.now()
        player = self._player_for_token(room, player_token)
        if (
            not self._session_is_active(room.expires_at, now)
            or player is None
            or not self._session_is_active(player.session_expires_at, now)
        ):
            raise DomainError("PLAYER_SESSION_REQUIRED", "需要有效的玩家工作階段。", 401)
        if not csrf_token or not hmac.compare_digest(player.csrf_token, csrf_token):
            raise DomainError("CSRF_FAILED", "CSRF 驗證失敗。", 403)
        return player

    @staticmethod
    def _session_is_active(expires_at: datetime | None, now: datetime) -> bool:
        return expires_at is not None and not is_expired_at(expires_at, now)

    @staticmethod
    def _player_for_token(room: Room, player_token: str | None) -> Player | None:
        if not player_token:
            return None
        token_hash = hash_session_token(player_token)
        return next(
            (item for item in room.players if item.session_hash and hmac.compare_digest(item.session_hash, token_hash)),
            None,
        )

    def _required_room(self, room_id: str) -> Room:
        room = self.repository.get(room_id)
        if room is None:
            raise DomainError("ROOM_NOT_FOUND", "找不到房間。", 404)
        return room

    @staticmethod
    def _check_version(room: Room, expected_version: int) -> None:
        if room.version != expected_version:
            raise DomainError("VERSION_CONFLICT", "房間狀態已更新，請重新載入。", 409)
