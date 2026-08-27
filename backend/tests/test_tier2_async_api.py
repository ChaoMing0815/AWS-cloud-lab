from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.application.security import hash_session_token
from app.domain.models import DiceResult, Room, World
from app.main import create_app


@dataclass(frozen=True)
class AcceptedJob:
    job_id: str


class RecordingProducer:
    def __init__(self, repository: MemoryRoomRepository) -> None:
        self.repository = repository
        self.calls: list[tuple[str, int, int, bool]] = []

    def begin(
        self,
        room_id: str,
        round_number: int,
        expected_version: int,
        skip_pending_spark: bool,
    ) -> AcceptedJob:
        self.calls.append(
            (room_id, round_number, expected_version, skip_pending_spark)
        )
        room = self.repository.get(room_id)
        assert room is not None
        room.status = "RESOLVING"
        room.version += 1
        self.repository.save(room)
        return AcceptedJob(job_id="job-opaque-7f2c")


class ForbiddenSynchronousStoryteller:
    def __init__(self) -> None:
        self.round_calls = 0

    def resolve_round(self, _room):
        self.round_calls += 1
        raise AssertionError("async request 不得在 Web process 呼叫 Storyteller")

    def resolve_ending(self, _room):
        raise AssertionError("async request 不得在 Web process 生成結局")


def resolving_room() -> Room:
    expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    return Room(
        id="room-async-1",
        room_code="ASYNC1",
        status="AWAITING_SPARK",
        version=7,
        round_number=2,
        world=World(
            name="非同步測試世界",
            story_title="非同步測試世界",
            premise="三位玩家需要等待獨立故事工作者完成回合敘事。",
            objective="完成可重播且不重複套用的回合結算。",
        ),
        host_session_hash=hash_session_token("host-token"),
        host_csrf_token="host-csrf",
        expires_at=expires_at,
        host_session_expires_at=expires_at,
        dice_results=[
            DiceResult(
                player_id="player-1",
                round_number=2,
                d6_1=4,
                d6_2=3,
                approach="insight",
                attribute_value=1,
                base_total=8,
                final_total=8,
                result="PARTIAL_SUCCESS",
                progress_delta=1,
                danger_delta=1,
                spark_decision="DECLINE",
            )
        ],
    )


def test_resolve_accepts_one_durable_job_without_storyteller_call_and_replays() -> None:
    repository = MemoryRoomRepository()
    repository.save(resolving_room())
    producer = RecordingProducer(repository)
    storyteller = ForbiddenSynchronousStoryteller()
    app = create_app(
        room_repository=repository,
        storyteller=storyteller,
        story_resolution_producer=producer,
    )

    with TestClient(app) as client:
        client.cookies.set("co_story_host", "host-token")
        request = {
            "json": {"skip_pending_spark": False, "room_version": 7},
            "headers": {
                "Idempotency-Key": "async-resolve-0001",
                "X-CSRF-Token": "host-csrf",
            },
        }
        first = client.post(
            "/api/v1/rooms/room-async-1/rounds/2:resolve",
            **request,
        )
        replay = client.post(
            "/api/v1/rooms/room-async-1/rounds/2:resolve",
            **request,
        )

    assert first.status_code == 202
    assert replay.status_code == 202
    assert first.json() == replay.json()
    assert first.json()["jobId"] == "job-opaque-7f2c"
    assert first.json()["room"]["status"] == "RESOLVING"
    assert first.json()["room"]["version"] == 8
    assert producer.calls == [("room-async-1", 2, 7, False)]
    assert storyteller.round_calls == 0


def test_async_resolve_keeps_host_and_csrf_guards_before_producer() -> None:
    repository = MemoryRoomRepository()
    repository.save(resolving_room())
    producer = RecordingProducer(repository)
    app = create_app(
        room_repository=repository,
        storyteller=ForbiddenSynchronousStoryteller(),
        story_resolution_producer=producer,
    )

    with TestClient(app) as client:
        client.cookies.set("co_story_host", "wrong-host-token")
        response = client.post(
            "/api/v1/rooms/room-async-1/rounds/2:resolve",
            json={"skip_pending_spark": False, "room_version": 7},
            headers={
                "Idempotency-Key": "async-resolve-unauthorized",
                "X-CSRF-Token": "wrong-csrf",
            },
        )

    assert response.status_code == 401
    assert producer.calls == []
