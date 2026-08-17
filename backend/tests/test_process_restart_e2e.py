from __future__ import annotations

import os
import socket
import subprocess
import time
from pathlib import Path

import httpx
import psycopg
import pytest

from app.adapters.postgres_migrations import apply_migrations
from app.adapters.postgres_room_repository import PostgresRoomRepository
from app.domain.models import Character, DiceResult, StoryEntry, World


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PYTHON = REPOSITORY_ROOT / ".venv" / "bin" / "python"


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def start_api_process(port: int, dsn: str) -> subprocess.Popen[str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = dsn
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
            raise AssertionError(f"Uvicorn process exited during startup: {output}")
        try:
            response = httpx.get(
                f"http://127.0.0.1:{port}/api/v1/health",
                timeout=0.25,
            )
            if response.status_code == 200:
                return process
        except httpx.HTTPError:
            pass
        time.sleep(0.05)
    stop_api_process(process)
    raise AssertionError("Uvicorn process did not become healthy within 10 seconds")


def stop_api_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if process.stdout:
        process.stdout.close()


@pytest.mark.skipif(
    "CO_STORY_PROCESS_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定 process restart 專用 PostgreSQL 測試資料庫",
)
def test_complete_room_and_session_survive_real_uvicorn_process_restart() -> None:
    dsn = os.environ["CO_STORY_PROCESS_TEST_DATABASE_URL"]
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM rooms")
    repository = PostgresRoomRepository(dsn)
    port = available_port()
    base_url = f"http://127.0.0.1:{port}"
    client = httpx.Client(base_url=base_url, timeout=3)

    first_process = start_api_process(port, dsn)
    try:
        created_response = client.post(
            "/api/v1/rooms",
            json={"nickname": "重啟驗證房主"},
            headers={"Idempotency-Key": "process-restart-create"},
        )
        assert created_response.status_code == 201
        created = created_response.json()
        room = repository.get(created["id"])
        assert room is not None
        room.status = "COLLECTING_ACTIONS"
        room.version = 12
        room.round_number = 3
        room.world = World(
            name="重啟後的月台",
            story_title="末班車仍在等待",
            premise="玩家必須在服務重啟後繼續共同任務。",
            objective="確認完整 canonical state 沒有遺失。",
            opening_scene="Uvicorn process 即將停止。",
            core_obstacle="記憶體狀態會全部消失。",
            tone="mystery",
        )
        room.initial_player_count = 3
        room.progress_points = 4
        room.danger_points = 2
        room.players[0].character = Character(
            name="守夜人",
            background="負責確認持久化證據。",
            trait="細心",
            weakness="過度確認",
            courage=1,
            insight=2,
            bond=0,
            spark=1,
        )
        room.entries = [
            StoryEntry(
                id="restart-entry-1",
                type="story",
                title="故事主持人",
                round_number=2,
                text="第一個 process 已保存這段故事。",
            )
        ]
        room.dice_results = [
            DiceResult(
                player_id=room.players[0].id,
                round_number=2,
                d6_1=4,
                d6_2=3,
                approach="insight",
                attribute_value=2,
                base_total=9,
                final_total=9,
                result="PARTIAL_SUCCESS",
                progress_delta=1,
                danger_delta=1,
                spark_decision="DECLINE",
            )
        ]
        repository.save(room)
        before_restart = client.get("/api/v1/rooms/current")
        assert before_restart.status_code == 200
        assert before_restart.json()["id"] == room.id
    finally:
        stop_api_process(first_process)

    second_process = start_api_process(port, dsn)
    try:
        restored_response = client.get("/api/v1/rooms/current")
        assert restored_response.status_code == 200
        restored = restored_response.json()
        assert restored["id"] == room.id
        assert restored["roomCode"] == room.room_code
        assert restored["round"] == 3
        assert restored["progressPoints"] == 4
        assert restored["dangerPoints"] == 2
        assert restored["players"][0]["character"]["name"] == "守夜人"
        assert restored["entries"][0]["text"] == "第一個 process 已保存這段故事。"
        assert restored["diceResults"][0]["result"] == "PARTIAL_SUCCESS"
        assert restored["session"]["isHost"] is True
        assert restored["session"]["playerId"] == room.players[0].id
    finally:
        stop_api_process(second_process)
        client.close()
