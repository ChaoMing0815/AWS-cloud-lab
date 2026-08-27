import importlib
import importlib.util

from app.adapters.mock_storyteller import MockStoryteller


def _narrator_module():
    spec = importlib.util.find_spec("app.adapters.story_resolution_narrator")
    assert spec is not None, "snapshot narrator adapter 尚未建立"
    return importlib.import_module("app.adapters.story_resolution_narrator")


def _worker_module():
    spec = importlib.util.find_spec("app.workers.story_resolution_worker")
    assert spec is not None, "獨立 story-resolution worker runner 尚未建立"
    return importlib.import_module("app.workers.story_resolution_worker")


def snapshot(*, round_number: int = 2, max_rounds: int = 6) -> dict:
    return {
        "operation": "resolve-round",
        "producer": {
            "source_room_version": 7,
            "skip_pending_spark": False,
        },
        "world": {
            "name": "霽霧之城",
            "story_title": "霽霧之城",
            "premise": "三位調查員必須讓城市重新看見晨光。",
            "objective": "重新點亮中央燈塔。",
            "opening_scene": "濃霧覆蓋中央廣場。",
            "core_obstacle": "燈塔機關已經鏽蝕。",
            "tone": "mystery",
            "custom_tone": None,
        },
        "canonical_state": {
            "round_number": round_number,
            "max_rounds": max_rounds,
            "progress_points_before_round": 2,
            "danger_points_before_round": 1,
            "progress_delta": 1,
            "danger_delta": 1,
        },
        "recent_story": [
            {
                "type": "narrator",
                "title": "故事主持人",
                "round_number": round_number - 1,
                "text": "調查員抵達鏽蝕的燈塔入口。",
            }
        ],
        "resolved_actions": [
            {
                "player_id": "player-1",
                "player_name": "凜",
                "role": "工程師",
                "action": "檢查鏽蝕機關的受力點",
                "approach": "insight",
                "character": {
                    "name": "凜",
                    "background": "熟悉機械結構。",
                    "trait": "細心",
                    "weakness": "過度確認",
                    "courage": 0,
                    "insight": 2,
                    "bond": 1,
                    "spark": 1,
                },
                "dice": {
                    "d6_1": 3,
                    "d6_2": 3,
                    "attribute_value": 2,
                    "base_total": 8,
                    "final_total": 8,
                    "result": "PARTIAL_SUCCESS",
                    "progress_delta": 1,
                    "danger_delta": 1,
                    "spark_used": 0,
                    "spark_decision": "DECLINE",
                },
            }
        ],
    }


def test_snapshot_narrator_rebuilds_only_public_story_context_and_final_ending() -> None:
    module = _narrator_module()
    narrator = module.StorytellerSnapshotNarrator(MockStoryteller())

    round_result = narrator.resolve(snapshot())
    final_result = narrator.resolve(snapshot(round_number=6, max_rounds=6))

    assert "檢查鏽蝕機關" in round_result["narration"]
    assert "ending_narration" not in round_result
    assert final_result["ending_narration"]
    assert "session" not in repr(round_result).lower()
    assert "csrf" not in repr(round_result).lower()


class NextJobQueue:
    def __init__(self, job_id: str | None) -> None:
        self.job_id = job_id
        self.calls = 0

    def next_available_job_id(self):
        self.calls += 1
        return self.job_id


class RecordingWorker:
    def __init__(self) -> None:
        self.calls = []

    def process(self, job_id, worker_id):
        self.calls.append((job_id, worker_id))
        return {"outcome": "applied"}


def test_local_worker_runner_processes_one_available_job_or_reports_idle() -> None:
    module = _worker_module()
    worker = RecordingWorker()
    active = module.LocalStoryResolutionWorkerRunner(
        NextJobQueue("job-1"),
        worker,
        worker_id="worker-process-1",
    )
    idle_queue = NextJobQueue(None)
    idle = module.LocalStoryResolutionWorkerRunner(
        idle_queue,
        worker,
        worker_id="worker-process-2",
    )

    assert active.run_once() == "processed"
    assert idle.run_once() == "idle"
    assert worker.calls == [("job-1", "worker-process-1")]
    assert idle_queue.calls == 1
