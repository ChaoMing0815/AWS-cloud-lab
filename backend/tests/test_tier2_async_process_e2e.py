from __future__ import annotations

import os
import socket
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import psycopg
import pytest

from app.adapters.postgres_migrations import apply_migrations
from app.adapters.postgres_room_repository import PostgresRoomRepository
from app.application.security import hash_session_token
from app.domain.models import Character, DiceResult, Player, Room, StoryEntry, World


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"
PYTHON = REPOSITORY_ROOT / ".venv" / "bin" / "python"


def _available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _start_api(port: int, dsn: str) -> subprocess.Popen[str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = dsn
    environment.pop("CO_STORY_ENV", None)
    process = subprocess.Popen(
        [
            str(PYTHON),
            "-m",
            "uvicorn",
            "app.main:app",
            "--app-dir",
            "backend",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise AssertionError(f"API process exited during startup: {output}")
        try:
            if httpx.get(
                f"http://127.0.0.1:{port}/api/v1/health",
                timeout=0.25,
            ).status_code == 200:
                return process
        except httpx.HTTPError:
            pass
        time.sleep(0.05)
    _stop_process(process)
    raise AssertionError("API process did not become healthy")


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if process.stdout:
        process.stdout.close()


def _room() -> Room:
    expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    player = Player(
        id="process-player-1",
        name="凜",
        role="工程師",
        action="檢查鏽蝕機關的受力點",
        action_approach="insight",
        character=Character(
            name="凜",
            background="熟悉機械結構。",
            trait="細心",
            weakness="過度確認",
            courage=0,
            insight=2,
            bond=1,
        ),
    )
    return Room(
        id="tier2-process-room",
        room_code="T2PROC",
        status="AWAITING_SPARK",
        version=7,
        round_number=2,
        world=World(
            name="霽霧之城",
            story_title="霽霧之城",
            premise="三位調查員必須讓城市重新看見晨光。",
            objective="重新點亮中央燈塔。",
            opening_scene="濃霧覆蓋中央廣場。",
            core_obstacle="燈塔機關已經鏽蝕。",
            tone="mystery",
        ),
        host_session_hash=hash_session_token("process-host-token"),
        host_csrf_token="process-host-csrf",
        expires_at=expires_at,
        host_session_expires_at=expires_at,
        initial_player_count=1,
        players=[player],
        entries=[
            StoryEntry(
                id="process-entry-1",
                type="narrator",
                title="故事主持人",
                round_number=1,
                text="調查員抵達鏽蝕的燈塔入口。",
            )
        ],
        dice_results=[
            DiceResult(
                player_id=player.id,
                round_number=2,
                d6_1=3,
                d6_2=3,
                approach="insight",
                attribute_value=2,
                base_total=8,
                final_total=8,
                result="PARTIAL_SUCCESS",
                progress_delta=1,
                danger_delta=1,
                spark_decision="DECLINE",
            )
        ],
    )


@pytest.mark.skipif(
    "CO_STORY_PROCESS_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定 process restart 專用 PostgreSQL 測試資料庫",
)
def test_web_and_worker_processes_complete_one_job_and_restart_without_replay() -> None:
    dsn = os.environ["CO_STORY_PROCESS_TEST_DATABASE_URL"]
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM story_completion_outbox")
        connection.execute("DELETE FROM story_result_inbox")
        connection.execute("DELETE FROM story_jobs")
        connection.execute("DELETE FROM rooms")
    repository = PostgresRoomRepository(dsn)
    repository.save(_room())
    port = _available_port()
    client = httpx.Client(
        base_url=f"http://127.0.0.1:{port}",
        timeout=3,
        cookies={
            "co_story_local_room": "tier2-process-room",
            "co_story_host": "process-host-token",
        },
    )

    first_api = _start_api(port, dsn)
    try:
        accepted = client.post(
            "/api/v1/rooms/tier2-process-room/rounds/2:resolve",
            json={"skip_pending_spark": False, "room_version": 7},
            headers={
                "Idempotency-Key": "tier2-process-resolve",
                "X-CSRF-Token": "process-host-csrf",
            },
        )
        assert accepted.status_code == 202
        assert accepted.json()["room"]["status"] == "RESOLVING"
    finally:
        _stop_process(first_api)

    environment = os.environ.copy()
    environment["DATABASE_URL"] = dsn
    environment.pop("CO_STORY_ENV", None)
    first_worker = subprocess.run(
        [str(PYTHON), "-m", "app.workers.story_resolution_worker"],
        cwd=BACKEND_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert first_worker.returncode == 0
    assert first_worker.stdout.strip() == "worker_result=processed"
    room_after_worker = repository.get("tier2-process-room")
    assert room_after_worker is not None
    assert room_after_worker.status == "COLLECTING_ACTIONS"
    assert room_after_worker.round_number == 3

    second_worker = subprocess.run(
        [str(PYTHON), "-m", "app.workers.story_resolution_worker"],
        cwd=BACKEND_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert second_worker.returncode == 0
    assert second_worker.stdout.strip() == "worker_result=idle"
    assert repository.get("tier2-process-room") == room_after_worker

    second_api = _start_api(port, dsn)
    try:
        restored = client.get("/api/v1/rooms/current")
        assert restored.status_code == 200
        assert restored.json()["status"] == "COLLECTING_ACTIONS"
        assert restored.json()["round"] == 3
    finally:
        _stop_process(second_api)
        client.close()
