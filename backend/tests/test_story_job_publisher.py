from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest


NOW = datetime(2026, 8, 29, 8, 0, tzinfo=timezone.utc)


class Clock:
    def now(self):
        return NOW


class Result:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None


class Connection:
    def __init__(self, script):
        self.script = list(script)
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        normalized = " ".join(sql.lower().split())
        self.statements.append((normalized, params))
        expected, rows = self.script.pop(0)
        assert expected in normalized
        return Result(rows)


def _outbox(monkeypatch, connection):
    from app.adapters import postgres_story_job_dispatch as module

    monkeypatch.setattr(module, "psycopg", SimpleNamespace(connect=lambda _dsn: connection))
    return module.PostgresStoryJobDispatchOutbox(
        "postgresql://test/ignored",
        clock=Clock(),
        lease_duration=timedelta(seconds=30),
        lease_token_factory=lambda: "lease-1",
    )


def test_outbox_claim_uses_skip_locked_and_reclaims_only_expired_leases(monkeypatch) -> None:
    connection = Connection(
        [("for update skip locked", [("job-1", {"schema_version": 1, "job_id": "job-1"})])]
    )

    claimed = _outbox(monkeypatch, connection).claim_one()

    assert claimed.job_id == "job-1"
    assert claimed.message_payload == {"schema_version": 1, "job_id": "job-1"}
    assert claimed.lease_token == "lease-1"
    sql, params = connection.statements[0]
    assert "status = 'pending'" in sql
    assert "status = 'publishing'" in sql
    assert "lease_expires_at <=" in sql
    assert "attempt_count = attempt_count + 1" in sql
    assert params == (NOW, "lease-1", NOW + timedelta(seconds=30), NOW)


def test_publisher_marks_dispatched_only_after_exact_sqs_send(monkeypatch) -> None:
    from app.application.story_job_publisher import StoryJobPublisher

    events = []
    delivery = SimpleNamespace(
        job_id="job-1",
        message_payload={"schema_version": 1, "job_id": "job-1"},
        lease_token="lease-1",
    )
    outbox = SimpleNamespace(
        claim_one=lambda: delivery,
        mark_dispatched=lambda job_id, token: events.append(("mark", job_id, token)),
        release=lambda *_args: events.append(("release",)),
    )
    transport = SimpleNamespace(
        publish=lambda job_id: events.append(("send", job_id)),
    )

    assert StoryJobPublisher(outbox, transport).run_once() == "published"
    assert events == [("send", "job-1"), ("mark", "job-1", "lease-1")]


def test_send_failure_releases_for_reconciliation_without_marking_dispatched() -> None:
    from app.application.story_job_publisher import StoryJobPublisher

    events = []
    delivery = SimpleNamespace(job_id="job-1", lease_token="lease-1")
    outbox = SimpleNamespace(
        claim_one=lambda: delivery,
        mark_dispatched=lambda *_args: events.append(("mark",)),
        release=lambda job_id, token, error_code: events.append(
            ("release", job_id, token, error_code)
        ),
    )

    def fail(_job_id):
        raise RuntimeError("provider detail must not persist")

    assert StoryJobPublisher(outbox, SimpleNamespace(publish=fail)).run_once() == "retry"
    assert events == [("release", "job-1", "lease-1", "sqs_send_failed")]


def test_mark_failure_leaves_publishing_lease_for_expiry_reconciliation() -> None:
    from app.application.story_job_publisher import StoryJobPublisher

    events = []
    delivery = SimpleNamespace(job_id="job-1", lease_token="lease-1")

    def mark_failed(_job_id, _token):
        events.append(("mark",))
        raise RuntimeError("database unavailable after successful send")

    outbox = SimpleNamespace(
        claim_one=lambda: delivery,
        mark_dispatched=mark_failed,
        release=lambda *_args: events.append(("release",)),
    )
    transport = SimpleNamespace(
        publish=lambda job_id: events.append(("send", job_id)),
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        StoryJobPublisher(outbox, transport).run_once()

    assert events == [("send", "job-1"), ("mark",)]


def test_publisher_is_idle_without_claim_and_never_sends() -> None:
    from app.application.story_job_publisher import StoryJobPublisher

    events = []
    outbox = SimpleNamespace(claim_one=lambda: None)
    transport = SimpleNamespace(publish=lambda _job_id: events.append("send"))

    assert StoryJobPublisher(outbox, transport).run_once() == "idle"
    assert events == []


def test_outbox_rejects_stale_lease_when_marking_dispatched(monkeypatch) -> None:
    from app.adapters.postgres_story_job_dispatch import StoryJobDispatchOwnershipConflict

    connection = Connection([("returning job_id", [])])
    outbox = _outbox(monkeypatch, connection)

    with pytest.raises(StoryJobDispatchOwnershipConflict):
        outbox.mark_dispatched("job-1", "stale-token")


def test_sqs_publish_sends_only_compact_opaque_job_signal() -> None:
    from app.adapters.sqs_story_job_transport import SqsStoryJobTransport

    calls = []
    client = SimpleNamespace(send_message=lambda **kwargs: calls.append(kwargs) or {})
    transport = SqsStoryJobTransport(
        client,
        queue_url="https://sqs.ap-northeast-1.amazonaws.com/example/story",
        visibility_timeout_seconds=180,
        wait_time_seconds=20,
    )

    transport.publish("job-opaque-1")

    assert calls == [
        {
            "QueueUrl": "https://sqs.ap-northeast-1.amazonaws.com/example/story",
            "MessageBody": '{"schema_version":1,"job_id":"job-opaque-1"}',
        }
    ]


@pytest.mark.parametrize("job_id", ["", " job-1", "job\n1", "x" * 129])
def test_sqs_publish_rejects_invalid_job_id_before_network(job_id) -> None:
    from app.adapters.sqs_story_job_transport import SqsStoryJobTransport

    calls = []
    client = SimpleNamespace(send_message=lambda **kwargs: calls.append(kwargs) or {})
    transport = SqsStoryJobTransport(
        client,
        queue_url="https://sqs.ap-northeast-1.amazonaws.com/example/story",
        visibility_timeout_seconds=180,
        wait_time_seconds=20,
    )

    with pytest.raises(ValueError, match="invalid_story_job_id"):
        transport.publish(job_id)

    assert calls == []
