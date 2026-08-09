from __future__ import annotations

import hmac
import secrets
import string
from uuid import uuid4

from app.application.ports import DiceRoller, IdempotencyStore, RoomRepository, SessionTokenFactory, Storyteller
from app.application.rules import (
    apply_spark,
    classify_result,
    ending_cost,
    ending_result,
    points_percent,
    target_points,
)
from app.application.security import hash_session_token
from app.domain.errors import DomainError
from app.domain.models import Character, DiceResult, Player, Room, StoryEntry, World

ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


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
    ) -> None:
        self.repository = repository
        self.storyteller = storyteller
        self.idempotency = idempotency
        self.token_factory = token_factory
        self.dice_roller = dice_roller
        self.demo_room_id = self._create_demo_room()

    def _create_demo_room(self) -> str:
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
        room = self.repository.get(self.demo_room_id)
        if room is None:
            raise RuntimeError("Demo room was not initialized")
        return room

    def create_room(self, idempotency_key: str) -> tuple[Room, str]:
        host_token = self.token_factory.derive("host-session", idempotency_key)
        host_csrf = self.token_factory.derive("host-csrf", idempotency_key)

        def operation() -> Room:
            room = Room(
                id=_new_id(),
                room_code=_room_code(),
                status="DRAFT",
                version=1,
                round_number=1,
                world=_empty_world(),
                host_session_hash=hash_session_token(host_token),
                host_csrf_token=host_csrf,
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

        room = self.idempotency.execute("create-room", idempotency_key, {}, operation)
        return room, host_token

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
            self.repository.save(current)
            return current

        payload = {**world_data, "max_rounds": max_rounds, "room_version": expected_version}
        return self.idempotency.execute(
            f"confirm-world:{room_id}", idempotency_key, payload, operation
        )

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
            self.repository.save(room)
            return room

        payload = {"nickname": nickname, "role": role, "room_version": expected_version}
        room = self.idempotency.execute(f"join-room:{room_id}", idempotency_key, payload, operation)
        return room, player_token

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
            if current.status not in {"AWAITING_SPARK", "RESOLVING"}:
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
                    text=self.storyteller.resolve_round(current),
                )
            )
            for player in current.players:
                player.action = ""
                player.action_approach = ""
            completed_round = current.round_number
            target = target_points(current.initial_player_count, current.max_rounds)
            progress_percent = points_percent(current.progress_points, target)
            danger_percent = points_percent(current.danger_points, target)
            if completed_round >= current.max_rounds:
                current.status = "COMPLETED"
                current.ending_result = ending_result(progress_percent)
                current.ending_cost = ending_cost(danger_percent)
            else:
                current.round_number += 1
                current.status = (
                    "COMPLETION_AVAILABLE"
                    if progress_percent >= 100
                    else "COLLECTING_ACTIONS"
                )
            current.version += 1
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
            if decision == "CONTINUE":
                current.status = "COLLECTING_ACTIONS"
            else:
                target = target_points(current.initial_player_count, current.max_rounds)
                current.ending_result = "FULL_SUCCESS"
                current.ending_cost = ending_cost(
                    points_percent(current.danger_points, target)
                )
                current.status = "COMPLETED"
                current.entries.append(
                    StoryEntry(
                        id=_new_id(),
                        type="ending",
                        title="故事結局",
                        round_number=current.round_number,
                        text=self.storyteller.resolve_ending(current),
                    )
                )
            current.version += 1
            self.repository.save(current)
            return current

        return self.idempotency.execute(
            f"finish-game:{room_id}",
            idempotency_key,
            {"decision": decision, "room_version": expected_version},
            operation,
        )

    def session_context(
        self,
        room: Room,
        host_token: str | None,
        player_token: str | None,
    ) -> dict:
        is_host = bool(
            host_token
            and room.host_session_hash
            and hmac.compare_digest(room.host_session_hash, hash_session_token(host_token))
        )
        player = self._player_for_token(room, player_token)
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
        return {
            "principalType": "anonymous",
            "playerId": None,
            "csrfToken": None,
            "isHost": False,
            "hostCsrfToken": None,
        }

    def _authorize_host(self, room: Room, host_token: str, csrf_token: str) -> None:
        if not host_token or not room.host_session_hash or not hmac.compare_digest(
            room.host_session_hash, hash_session_token(host_token)
        ):
            raise DomainError("HOST_SESSION_REQUIRED", "需要有效的房主工作階段。", 401)
        if not csrf_token or not hmac.compare_digest(room.host_csrf_token, csrf_token):
            raise DomainError("CSRF_FAILED", "CSRF 驗證失敗。", 403)

    def _authorize_player(self, room: Room, player_token: str, csrf_token: str) -> Player:
        player = self._player_for_token(room, player_token)
        if player is None:
            raise DomainError("PLAYER_SESSION_REQUIRED", "需要有效的玩家工作階段。", 401)
        if not csrf_token or not hmac.compare_digest(player.csrf_token, csrf_token):
            raise DomainError("CSRF_FAILED", "CSRF 驗證失敗。", 403)
        return player

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
