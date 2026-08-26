from __future__ import annotations

import importlib
import importlib.util


def _domain():
    spec = importlib.util.find_spec("app.domain.story_jobs")
    assert spec is not None, "story job domain contract 尚未建立"
    return importlib.import_module("app.domain.story_jobs")


def _application():
    spec = importlib.util.find_spec("app.application.story_jobs")
    assert spec is not None, "story job application contract 尚未建立"
    return importlib.import_module("app.application.story_jobs")


def test_factory_links_job_to_room_round_version_and_canonical_identity() -> None:
    domain = _domain()
    application = _application()

    job = application.create_story_job(
        operation=domain.StoryJobOperation.RESOLVE_ROUND,
        room_id="room-7",
        round_number=3,
        room_version=11,
        payload={"actions": [{"player_id": "p1", "text": "觀察門鎖"}]},
        job_id="job-1",
    )

    assert job.job_id == "job-1"
    assert job.idempotency_key == "story:resolve-round:room-7:round:3:version:11"
    assert job.room_id == "room-7"
    assert job.round_number == 3
    assert job.room_version == 11
    assert job.status is domain.StoryJobStatus.PENDING
    assert job.claimed_by is None
    assert job.attempt_count == 0
    assert job.result is None


def test_factory_rejects_invalid_room_coordinates() -> None:
    domain = _domain()
    application = _application()

    for room_id, round_number, room_version in (("", 1, 0), ("room-1", 0, 0), ("room-1", 1, -1)):
        try:
            application.create_story_job(
                operation=domain.StoryJobOperation.RESOLVE_ROUND,
                room_id=room_id,
                round_number=round_number,
                room_version=room_version,
                payload={},
                job_id="job-invalid",
            )
        except ValueError:
            pass
        else:
            raise AssertionError("invalid Room／round／version 應被拒絕")


def test_factory_owns_a_payload_snapshot() -> None:
    domain = _domain()
    application = _application()
    payload = {"actions": [{"text": "原始行動"}]}

    job = application.create_story_job(
        operation=domain.StoryJobOperation.RESOLVE_ROUND,
        room_id="room-1",
        round_number=1,
        room_version=2,
        payload=payload,
        job_id="job-snapshot",
    )
    payload["actions"][0]["text"] = "外部竄改"

    assert job.payload == {"actions": [{"text": "原始行動"}]}
