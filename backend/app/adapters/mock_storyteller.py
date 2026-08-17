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
        names = "、".join(player.name for player in room.players)
        results = [
            result
            for result in room.dice_results
            if result.round_number == room.round_number
        ]
        success_count = sum(result.result == "SUCCESS" for result in results)
        partial_count = sum(result.result == "PARTIAL_SUCCESS" for result in results)
        failure_count = sum(result.result == "FAILURE" for result in results)
        return (
            f"{names} 的選擇串成一套完整方案。"
            f"本回合共有 {success_count} 次成功、{partial_count} 次部分成功與 {failure_count} 次失敗。"
            "Mock 故事主持人依固定判定推進場景，沒有修改任何規則狀態。"
        )

    def resolve_ending(self, room: Room) -> str:
        result_labels = {
            "FULL_SUCCESS": "完整成功",
            "PARTIAL_SUCCESS": "部分成功",
            "FAILURE": "主要目標失敗",
        }
        cost_labels = {
            "LOW": "低代價",
            "SIGNIFICANT": "明確代價",
            "MAJOR": "重大代價",
        }
        return (
            f"故事以{result_labels[room.ending_result or 'FAILURE']}收束，"
            f"並付出{cost_labels[room.ending_cost or 'LOW']}。"
            "Mock 故事主持人只描述既定結局，沒有修改規則狀態。"
        )
