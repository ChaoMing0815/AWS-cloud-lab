from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from typing import Any


class InvalidStoryJobMessage(ValueError):
    pass


class VisibilityHeartbeatError(RuntimeError):
    pass


@dataclass(frozen=True)
class SqsStoryJobDelivery:
    job_id: str
    receipt_handle: str


class SqsStoryJobTransport:
    def __init__(
        self,
        client: Any,
        *,
        queue_url: str,
        visibility_timeout_seconds: int,
        wait_time_seconds: int,
    ) -> None:
        if not queue_url:
            raise ValueError("queue_url must not be empty")
        if not 1 <= visibility_timeout_seconds <= 43_200:
            raise ValueError("visibility_timeout_seconds must be between 1 and 43200")
        if not 1 <= wait_time_seconds <= 20:
            raise ValueError("wait_time_seconds must be between 1 and 20")
        self._client = client
        self._queue_url = queue_url
        self._visibility_timeout_seconds = visibility_timeout_seconds
        self._wait_time_seconds = wait_time_seconds

    def publish(self, job_id: str) -> None:
        if not _valid_job_id(job_id):
            raise ValueError("invalid_story_job_id")
        self._client.send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(
                {"schema_version": 1, "job_id": job_id},
                separators=(",", ":"),
            ),
        )

    def receive_one(self) -> SqsStoryJobDelivery | None:
        response = self._client.receive_message(
            QueueUrl=self._queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=self._wait_time_seconds,
            VisibilityTimeout=self._visibility_timeout_seconds,
        )
        messages = response.get("Messages", [])
        if not messages:
            return None
        if not isinstance(messages, list) or len(messages) != 1:
            raise InvalidStoryJobMessage("invalid_story_job_message")
        message = messages[0]
        if not isinstance(message, dict):
            raise InvalidStoryJobMessage("invalid_story_job_message")
        receipt_handle = message.get("ReceiptHandle")
        body = message.get("Body")
        if not isinstance(receipt_handle, str) or not receipt_handle:
            raise InvalidStoryJobMessage("invalid_story_job_message")
        if not isinstance(body, str):
            raise InvalidStoryJobMessage("invalid_story_job_message")
        try:
            payload = json.loads(body)
        except (TypeError, ValueError) as exc:
            raise InvalidStoryJobMessage("invalid_story_job_message") from exc
        if not isinstance(payload, dict) or set(payload) != {"schema_version", "job_id"}:
            raise InvalidStoryJobMessage("invalid_story_job_message")
        schema_version = payload["schema_version"]
        job_id = payload["job_id"]
        if (
            not isinstance(schema_version, int)
            or isinstance(schema_version, bool)
            or schema_version != 1
        ):
            raise InvalidStoryJobMessage("invalid_story_job_message")
        if not _valid_job_id(job_id):
            raise InvalidStoryJobMessage("invalid_story_job_message")
        return SqsStoryJobDelivery(job_id=job_id, receipt_handle=receipt_handle)

    def extend_visibility(self, delivery: SqsStoryJobDelivery) -> None:
        self._client.change_message_visibility(
            QueueUrl=self._queue_url,
            ReceiptHandle=delivery.receipt_handle,
            VisibilityTimeout=self._visibility_timeout_seconds,
        )

    def delete(self, delivery: SqsStoryJobDelivery) -> None:
        self._client.delete_message(
            QueueUrl=self._queue_url,
            ReceiptHandle=delivery.receipt_handle,
        )

    def visibility_heartbeat(
        self,
        delivery: SqsStoryJobDelivery,
        *,
        interval_seconds: int = 60,
    ) -> "SqsVisibilityHeartbeat":
        return SqsVisibilityHeartbeat(
            self,
            delivery,
            interval_seconds=interval_seconds,
        )


class SqsVisibilityHeartbeat:
    def __init__(
        self,
        transport: Any,
        delivery: SqsStoryJobDelivery,
        *,
        interval_seconds: int,
        stop_event: Any | None = None,
        thread_factory: Any | None = None,
    ) -> None:
        if interval_seconds < 1:
            raise ValueError("interval_seconds must be positive")
        self._transport = transport
        self._delivery = delivery
        self._interval_seconds = interval_seconds
        self._stop_event = stop_event or threading.Event()
        self._thread_factory = thread_factory or threading.Thread
        self._thread: Any | None = None
        self._error: Exception | None = None

    def __enter__(self) -> "SqsVisibilityHeartbeat":
        self._thread = self._thread_factory(
            target=self._run,
            name="co-story-sqs-visibility-heartbeat",
            daemon=True,
        )
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()
        if self._error is not None and exc_type is None:
            raise VisibilityHeartbeatError("visibility_heartbeat_failed") from None
        return False

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval_seconds):
            try:
                self._transport.extend_visibility(self._delivery)
            except Exception as exc:
                self._error = exc
                return


def _valid_job_id(value: object) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        return False
    return all(not character.isspace() and ord(character) >= 32 for character in value)
