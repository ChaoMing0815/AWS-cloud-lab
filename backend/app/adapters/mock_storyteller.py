from app.application.ports import Storyteller
from app.domain.models import Room


class MockStoryteller(Storyteller):
    def resolve_round(self, room: Room) -> str:
        names = "、".join(player.name for player in room.players)
        return (
            f"{names} 的選擇串成一套完整方案。"
            "Mock 故事主持人已收到所有行動；正式骰子、星火與 Bedrock 敘事將由後續 adapter 實作。"
        )
