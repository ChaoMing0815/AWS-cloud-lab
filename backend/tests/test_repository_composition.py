import inspect

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.main import create_app


def test_create_app_accepts_and_uses_room_repository_dependency() -> None:
    signature = inspect.signature(create_app)

    assert "room_repository" in signature.parameters

    repository = MemoryRoomRepository()
    app = create_app(room_repository=repository)

    assert app.state.room_service.repository is repository
