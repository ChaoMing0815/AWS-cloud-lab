import importlib
import importlib.util
import os

import pytest
import psycopg

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.adapters.postgres_migrations import apply_migrations
from app.adapters.postgres_room_repository import PostgresRoomRepository
from app.application.ports import RoomRepository
from app.domain.models import Character, DiceResult, Player, Room, StoryEntry, World


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


@pytest.fixture(params=("memory", "postgres"))
def repository(request: pytest.FixtureRequest) -> RoomRepository:
    if request.param == "memory":
        return MemoryRoomRepository()

    dsn = os.environ.get("CO_STORY_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("需要明確指定專題 PostgreSQL 測試資料庫")
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM rooms")
    return PostgresRoomRepository(dsn)


def complete_room() -> Room:
    return Room(
        id="room-contract-1",
        room_code="ABC234",
        status="AWAITING_SPARK",
        version=8,
        round_number=2,
        world=World(
            name="午夜捷運",
            story_title="抵達終點前的提案",
            premise="三位玩家在末班車上完成提案。",
            objective="在抵達終點前送出提案。",
            opening_scene="車門關上，倒數四站。",
            core_obstacle="資料彼此矛盾。",
            tone="workplace_satire",
        ),
        host_session_hash="host-hash",
        host_csrf_token="host-csrf",
        max_rounds=6,
        initial_player_count=3,
        progress_points=5,
        danger_points=3,
        players=[
            Player(
                id="player-1",
                name="小林",
                role="資料分析師",
                action="我核對預算差異。",
                action_approach="insight",
                session_hash="player-hash",
                csrf_token="player-csrf",
                character=Character(
                    name="林析",
                    background="負責找出數字矛盾。",
                    trait="細心",
                    weakness="猶豫",
                    courage=0,
                    insight=2,
                    bond=1,
                    spark=1,
                ),
            )
        ],
        entries=[
            StoryEntry(
                id="entry-1",
                type="story",
                title="故事主持人",
                round_number=1,
                text="列車駛入隧道。",
            )
        ],
        dice_results=[
            DiceResult(
                player_id="player-1",
                round_number=1,
                d6_1=4,
                d6_2=3,
                approach="insight",
                attribute_value=2,
                base_total=9,
                final_total=10,
                result="SUCCESS",
                progress_delta=2,
                danger_delta=0,
                spark_used=1,
                spark_decision="USE",
            )
        ],
    )


def assert_save_succeeds(repository: RoomRepository, room: Room) -> None:
    error = None
    try:
        repository.save(room)
    except Exception as caught:  # contract 以 assertion 呈現 adapter 缺口
        error = caught

    assert error is None, f"repository.save 尚未保存 Room：{type(error).__name__}"


def test_room_repository_round_trips_complete_aggregate_and_returns_copies(
    repository: RoomRepository,
) -> None:
    expected = complete_room()
    assert_save_succeeds(repository, expected)

    expected.status = "MUTATED_AFTER_SAVE"
    restored = repository.get("room-contract-1")

    assert restored == complete_room()
    assert repository.get_by_code("ABC234") == complete_room()
    assert repository.get("missing-room") is None
    assert repository.get_by_code("ZZZZZZ") is None

    assert restored is not None
    restored.players[0].name = "MUTATED_AFTER_GET"
    assert repository.get("room-contract-1") == complete_room()


def test_room_repository_updates_existing_aggregate(repository: RoomRepository) -> None:
    room = complete_room()
    assert_save_succeeds(repository, room)
    room.version = 9
    room.status = "COLLECTING_ACTIONS"
    room.round_number = 3
    room.progress_points = 7
    room.entries.append(
        StoryEntry(
            id="entry-2",
            type="story",
            title="故事主持人",
            round_number=2,
            text="三人完成第一版提案。",
        )
    )
    assert_save_succeeds(repository, room)

    restored = repository.get(room.id)

    assert restored == room


def test_repository_delete_rolls_back_when_callback_raises(repository: RoomRepository) -> None:
    room = complete_room()
    assert_save_succeeds(repository, room)
    assert hasattr(repository, "delete"), "RoomRepository.delete 尚未建立"

    with pytest.raises(RuntimeError, match="abort deletion"):
        repository.delete(room.id, lambda _room: (_ for _ in ()).throw(RuntimeError("abort deletion")))

    assert repository.get(room.id) == room
