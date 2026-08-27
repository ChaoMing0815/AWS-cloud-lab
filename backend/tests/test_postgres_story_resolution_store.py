import importlib
import importlib.util
from pathlib import Path


def _module():
    spec = importlib.util.find_spec("app.adapters.postgres_story_resolution_store")
    assert spec is not None, "PostgreSQL story resolution coordinator 尚未建立"
    return importlib.import_module("app.adapters.postgres_story_resolution_store")


def test_postgres_coordinator_source_guards_atomic_producer_and_result_transactions() -> None:
    module = _module()
    source = Path(module.__file__).read_text(encoding="utf-8").lower()

    assert "for update" in source
    assert "insert into story_jobs" in source
    assert "insert into story_result_inbox" in source
    assert "insert into story_completion_outbox" in source
    assert "ownership_token" in source
    assert "lease_expires_at" in source
    assert "result_fingerprint" in source
    assert "room.version != job.room_version" in source
    assert source.index("insert into story_result_inbox") < source.index("mark_completion_dispatched")
