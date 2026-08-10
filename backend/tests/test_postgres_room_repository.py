import importlib
import importlib.util
import os

import pytest

from app.application.ports import RoomRepository


@pytest.mark.skipif(
    "CO_STORY_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定專題 PostgreSQL 測試資料庫",
)
def test_postgres_room_repository_implements_application_port() -> None:
    spec = importlib.util.find_spec("app.adapters.postgres_room_repository")
    assert spec is not None, "PostgresRoomRepository 尚未建立"

    module = importlib.import_module("app.adapters.postgres_room_repository")
    repository = module.PostgresRoomRepository(os.environ["CO_STORY_TEST_DATABASE_URL"])

    assert isinstance(repository, RoomRepository)
