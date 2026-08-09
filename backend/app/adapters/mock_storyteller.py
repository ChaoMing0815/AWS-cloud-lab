from app.application.ports import Storyteller
from app.domain.models import Room


class MockStoryteller(Storyteller):
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
