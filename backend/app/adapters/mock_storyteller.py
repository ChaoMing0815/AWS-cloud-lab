from app.application.ports import Storyteller
from app.domain.models import Room, World


class MockStoryteller(Storyteller):
    def generate_world(
        self,
        keywords: list[str],
        tone: str,
        custom_tone: str | None,
        supplemental_request: str | None,
    ) -> World:
        subject = "、".join(keywords)
        request = supplemental_request or "讓玩家共同補完關鍵細節。"
        return World(
            name=f"{keywords[0]}計畫",
            story_title=f"{keywords[0]}的共同任務",
            premise=(
                f"圍繞{subject}接連發生的異常狀況，所有玩家必須在有限時間內合作找出真相，"
                "並決定是否相信彼此帶來的關鍵線索。"
            ),
            objective=f"在有限時間內完成與{keywords[0]}有關的共同目標。",
            opening_scene=f"故事開始時，{keywords[0]}突然讓所有既有安排失效。",
            core_obstacle=f"關鍵線索被{keywords[-1]}遮蔽，團隊必須協調不同立場。",
            tone=tone,
            custom_tone=custom_tone,
        )

    def resolve_round(self, room: Room) -> str:
        results = [
            result
            for result in room.dice_results
            if result.round_number == room.round_number
        ]
        players_by_id = {player.id: player for player in room.players}
        previous_scene = _previous_scene(room)
        lines = [f"承接上一幕：{previous_scene}"]
        approach_labels = {"courage": "勇氣", "insight": "洞察", "bond": "連結"}
        for result in results:
            player = players_by_id[result.player_id]
            character = player.character
            if character is None:
                continue
            action = player.action.rstrip("。！？!?；; ")
            consequence = _round_consequence(room, character.weakness, result.result)
            deltas = _delta_text(result.progress_delta, result.danger_delta)
            spark = f"+星火{result.spark_used}" if result.spark_used else ""
            lines.append(
                f"{character.name}（{character.trait}；弱點：{character.weakness}）{action}；"
                f"骰點 {result.d6_1}+{result.d6_2}+"
                f"{approach_labels.get(result.approach, result.approach)}{result.attribute_value}{spark}="
                f"{result.final_total}，{consequence}（{deltas}）。"
            )
        progress_delta = sum(result.progress_delta for result in results)
        danger_delta = sum(result.danger_delta for result in results)
        success_count = sum(result.result == "SUCCESS" for result in results)
        partial_count = sum(result.result == "PARTIAL_SUCCESS" for result in results)
        failure_count = sum(result.result == "FAILURE" for result in results)
        lines.append(
            f"本回合固定結算為 {success_count} 次成功、{partial_count} 次部分成功與 "
            f"{failure_count} 次失敗，共增加進度 {progress_delta}、危機 {danger_delta}；下一幕，"
            f"團隊必須承接上述突破與牽制，在危機擴大前繼續朝「{room.world.objective}」行動。"
        )
        return "\n".join(lines)

    def resolve_ending(self, room: Room) -> str:
        result_consequences = {
            "FULL_SUCCESS": f"團隊完成了「{room.world.objective}」，主要目標成為可見成果。",
            "PARTIAL_SUCCESS": (
                f"團隊只完成「{room.world.objective}」的核心部分，仍有關鍵缺口尚未補上。"
            ),
            "FAILURE": (
                f"團隊未能完成「{room.world.objective}」，先前累積的阻礙成為主要目標失敗的直接後果。"
            ),
        }
        cost_consequences = {
            "LOW": "這項結果只留下低代價：團隊仍需整理現場，但沒有重要成果因此失去。",
            "SIGNIFICANT": "這項結果伴隨明確代價：上一幕留下的風險成為必須立刻處理的未解問題。",
            "MAJOR": "這項結果付出重大代價：團隊失去重要成果，危機留下難以逆轉的長期後果。",
        }
        result = room.ending_result or "FAILURE"
        cost = room.ending_cost or "LOW"
        result_labels = {"FULL_SUCCESS": "完整成功", "PARTIAL_SUCCESS": "部分成功", "FAILURE": "主要目標失敗"}
        cost_labels = {"LOW": "低代價", "SIGNIFICANT": "明確代價", "MAJOR": "重大代價"}
        previous_scene = _previous_scene(room)
        return (
            f"承接最後事件：{previous_scene}"
            f"{result_consequences[result]}"
            f"{cost_consequences[cost]}"
            f"最終固定狀態為進度 {room.progress_points}、危機 {room.danger_points}；"
            f"故事沒有改判規則引擎的{result_labels[result]}與{cost_labels[cost]}。"
        )


def _round_consequence(room: Room, weakness: str, result: str) -> str:
    if result == "SUCCESS":
        return f"行動成功，這項行動形成可見突破，讓「{room.world.objective}」向前推進"
    if result == "PARTIAL_SUCCESS":
        return f"部分成功，這項行動帶來進展，但「{weakness}」使新的牽制浮現"
    return "行動失敗，這項行動沒有達成預期並讓眼前阻礙惡化，但仍留下可繼續嘗試的線索"


def _delta_text(progress_delta: int, danger_delta: int) -> str:
    parts = []
    if progress_delta:
        parts.append(f"進度 +{progress_delta}")
    if danger_delta:
        parts.append(f"危機 +{danger_delta}")
    return "、".join(parts) or "進度 +0、危機 +0"


def _previous_scene(room: Room) -> str:
    narratives = [entry for entry in room.entries if entry.type in {"narrator", "ending"}]
    return narratives[-1].text if narratives else room.world.opening_scene
