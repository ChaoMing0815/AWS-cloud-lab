from app.application.ports import RoomRepository
from app.domain.models import Room


class PostgresRoomRepository(RoomRepository):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def get(self, room_id: str) -> Room | None:
        return None

    def get_by_code(self, room_code: str) -> Room | None:
        return None

    def save(self, room: Room) -> None:
        raise NotImplementedError
