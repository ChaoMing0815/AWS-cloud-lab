from __future__ import annotations

import importlib
import importlib.util
import json
from dataclasses import replace

import pytest

from app.application.story_jobs import create_story_job
from app.domain.story_jobs import StoryJobOperation, StoryJobStatus


def _transport_module():
    spec = importlib.util.find_spec("app.adapters.sqs_story_job_transport")
    assert spec is not None, "SQS story-job transport adapter 尚未建立"
    return importlib.import_module("app.adapters.sqs_story_job_transport")


def _worker_module():
    spec = importlib.util.find_spec("app.workers.story_resolution_worker")
    assert spec is not None
    return importlib.import_module("app.workers.story_resolution_worker")


class FakeSqsClient:
    def __init__(self, response=None) -> None:
        self.response = response or {}
        self.receive_calls = []
        self.delete_calls = []
        self.visibility_calls = []

    def receive_message(self, **kwargs):
        self.receive_calls.append(kwargs)
        return self.response

    def delete_message(self, **kwargs):
        self.delete_calls.append(kwargs)
        return {}

    def change_message_visibility(self, **kwargs):
        self.visibility_calls.append(kwargs)
        return {}


def _message(body: object, *, receipt_handle: str = "receipt-1") -> dict:
    return {
        "Messages": [
            {
                "Body": body if isinstance(body, str) else json.dumps(body),
                "ReceiptHandle": receipt_handle,
            }
        ]
    }


def _transport(client: FakeSqsClient):
    module = _transport_module()
    return module.SqsStoryJobTransport(
        client,
        queue_url="https://sqs.ap-northeast-1.amazonaws.com/example/story",
        visibility_timeout_seconds=180,
        wait_time_seconds=20,
    )


def test_receive_uses_bounded_long_poll_and_accepts_only_opaque_job_signal() -> None:
    client = FakeSqsClient(_message({"schema_version": 1, "job_id": "job-opaque-1"}))
    transport = _transport(client)

    delivery = transport.receive_one()

    assert delivery.job_id == "job-opaque-1"
    assert delivery.receipt_handle == "receipt-1"
    assert client.receive_calls == [
        {
            "QueueUrl": "https://sqs.ap-northeast-1.amazonaws.com/example/story",
            "MaxNumberOfMessages": 1,
            "WaitTimeSeconds": 20,
            "VisibilityTimeout": 180,
        }
    ]
    assert client.delete_calls == []


def test_receive_returns_none_when_long_poll_has_no_delivery() -> None:
    client = FakeSqsClient({})

    assert _transport(client).receive_one() is None
    assert client.delete_calls == []


@pytest.mark.parametrize(
    "body",
    [
        "not-json",
        [],
        {"schema_version": True, "job_id": "job-1"},
        {"schema_version": 2, "job_id": "job-1"},
        {"schema_version": 1},
        {"schema_version": 1, "job_id": ""},
        {"schema_version": 1, "job_id": " job-1"},
        {"schema_version": 1, "job_id": "x" * 129},
        {"schema_version": 1, "job_id": "job-1", "room": {"secret": "forbidden"}},
    ],
)
def test_invalid_or_expanded_message_schema_fails_closed_without_ack(body) -> None:
    client = FakeSqsClient(_message(body))
    transport = _transport(client)
    module = _transport_module()

    with pytest.raises(module.InvalidStoryJobMessage, match="invalid_story_job_message"):
        transport.receive_one()

    assert client.delete_calls == []
    assert client.visibility_calls == []


def test_missing_receipt_handle_fails_closed_without_echoing_payload() -> None:
    client = FakeSqsClient(_message({"schema_version": 1, "job_id": "job-1"}, receipt_handle=""))
    transport = _transport(client)
    module = _transport_module()

    with pytest.raises(module.InvalidStoryJobMessage) as captured:
        transport.receive_one()

    assert str(captured.value) == "invalid_story_job_message"
    assert "job-1" not in str(captured.value)


def test_delete_and_visibility_extension_are_scoped_to_exact_receipt() -> None:
    client = FakeSqsClient(_message({"schema_version": 1, "job_id": "job-1"}))
    transport = _transport(client)
    delivery = transport.receive_one()

    transport.extend_visibility(delivery)
    transport.delete(delivery)

    expected = {
        "QueueUrl": "https://sqs.ap-northeast-1.amazonaws.com/example/story",
        "ReceiptHandle": "receipt-1",
    }
    assert client.visibility_calls == [{**expected, "VisibilityTimeout": 180}]
    assert client.delete_calls == [expected]


class StepStopEvent:
    def __init__(self) -> None:
        self.wait_calls = []
        self.set_calls = 0

    def wait(self, timeout: float) -> bool:
        self.wait_calls.append(timeout)
        return len(self.wait_calls) > 1

    def set(self) -> None:
        self.set_calls += 1


class ImmediateThread:
    def __init__(self, *, target, name: str, daemon: bool) -> None:
        self._target = target
        self.name = name
        self.daemon = daemon
        self.started = False
        self.joined = False

    def start(self) -> None:
        self.started = True
        self._target()

    def join(self) -> None:
        self.joined = True


class VisibilityRecordingTransport:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.calls = []
        self.error = error

    def extend_visibility(self, delivery) -> None:
        self.calls.append(delivery)
        if self.error is not None:
            raise self.error


def test_visibility_heartbeat_extends_in_background_and_stops_cleanly() -> None:
    module = _transport_module()
    delivery = _delivery()
    transport = VisibilityRecordingTransport()
    stop_event = StepStopEvent()
    threads = []

    def thread_factory(**kwargs):
        thread = ImmediateThread(**kwargs)
        threads.append(thread)
        return thread

    with module.SqsVisibilityHeartbeat(
        transport,
        delivery,
        interval_seconds=60,
        stop_event=stop_event,
        thread_factory=thread_factory,
    ):
        pass

    assert transport.calls == [delivery]
    assert stop_event.wait_calls == [60, 60]
    assert stop_event.set_calls == 1
    assert threads[0].started is True
    assert threads[0].joined is True
    assert threads[0].daemon is True


def test_visibility_heartbeat_surfaces_extension_failure_without_receipt_data() -> None:
    module = _transport_module()
    delivery = _delivery()
    transport = VisibilityRecordingTransport(error=RuntimeError("receipt-sensitive-detail"))

    with pytest.raises(module.VisibilityHeartbeatError) as captured:
        with module.SqsVisibilityHeartbeat(
            transport,
            delivery,
            interval_seconds=60,
            stop_event=StepStopEvent(),
            thread_factory=lambda **kwargs: ImmediateThread(**kwargs),
        ):
            pass

    assert str(captured.value) == "visibility_heartbeat_failed"
    assert "receipt-sensitive-detail" not in str(captured.value)


class RecordingHeartbeat:
    def __init__(self, events: list[str], *, fail_on_exit: bool = False) -> None:
        self._events = events
        self._fail_on_exit = fail_on_exit

    def __enter__(self):
        self._events.append("heartbeat-enter")
        return self

    def __exit__(self, exc_type, exc, traceback):
        self._events.append("heartbeat-exit")
        if self._fail_on_exit and exc is None:
            raise RuntimeError("visibility_heartbeat_failed")
        return False


class RecordingTransport:
    def __init__(self, delivery, events: list[str]) -> None:
        self.delivery = delivery
        self.events = events

    def receive_one(self):
        self.events.append("receive")
        return self.delivery

    def delete(self, delivery) -> None:
        assert delivery is self.delivery
        self.events.append("delete")


class RecordingWorker:
    def __init__(self, result, events: list[str], *, error: Exception | None = None) -> None:
        self.result = result
        self.events = events
        self.error = error
        self.calls = []

    def process(self, job_id, worker_id):
        self.events.append("process")
        self.calls.append((job_id, worker_id))
        if self.error is not None:
            raise self.error
        return self.result


def _delivery():
    module = _transport_module()
    return module.SqsStoryJobDelivery(job_id="job-1", receipt_handle="receipt-1")


def _runner(transport, worker, events, *, heartbeat_failure: bool = False):
    module = _worker_module()
    return module.SqsStoryResolutionWorkerRunner(
        transport,
        worker,
        worker_id="worker-1",
        heartbeat_factory=lambda _delivery: RecordingHeartbeat(
            events,
            fail_on_exit=heartbeat_failure,
        ),
    )


def test_sqs_runner_deletes_only_after_processing_and_heartbeat_stop() -> None:
    events = []
    delivery = _delivery()
    transport = RecordingTransport(delivery, events)
    worker = RecordingWorker(object(), events)

    assert _runner(transport, worker, events).run_once() == "processed"
    assert worker.calls == [("job-1", "worker-1")]
    assert events == ["receive", "heartbeat-enter", "process", "heartbeat-exit", "delete"]


def test_sqs_runner_does_not_delete_on_processing_exception() -> None:
    events = []
    delivery = _delivery()
    transport = RecordingTransport(delivery, events)
    worker = RecordingWorker(None, events, error=RuntimeError("database_unavailable"))

    with pytest.raises(RuntimeError, match="database_unavailable"):
        _runner(transport, worker, events).run_once()

    assert "delete" not in events


def test_sqs_runner_keeps_delivery_for_retryable_story_failure() -> None:
    events = []
    delivery = _delivery()
    transport = RecordingTransport(delivery, events)
    pending = replace(
        create_story_job(
            operation=StoryJobOperation.RESOLVE_ROUND,
            room_id="room-1",
            round_number=1,
            room_version=1,
            payload={"snapshot": "sealed"},
            job_id="job-1",
        ),
        status=StoryJobStatus.PENDING,
    )
    worker = RecordingWorker(pending, events)

    assert _runner(transport, worker, events).run_once() == "retry"
    assert "delete" not in events


def test_sqs_runner_does_not_delete_when_visibility_heartbeat_fails() -> None:
    events = []
    delivery = _delivery()
    transport = RecordingTransport(delivery, events)
    worker = RecordingWorker(object(), events)

    with pytest.raises(RuntimeError, match="visibility_heartbeat_failed"):
        _runner(transport, worker, events, heartbeat_failure=True).run_once()

    assert "delete" not in events


def test_sqs_runner_reports_idle_without_starting_heartbeat() -> None:
    events = []
    transport = RecordingTransport(None, events)
    worker = RecordingWorker(object(), events)

    assert _runner(transport, worker, events).run_once() == "idle"
    assert events == ["receive"]
