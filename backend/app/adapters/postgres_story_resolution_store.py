from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import psycopg
from psycopg.types.json import Jsonb

from app.adapters.postgres_room_repository import PostgresRoomRepository, _room_from_payload
from app.application.ports import Clock, StoryResolutionStore
from app.application.story_jobs import create_story_job, story_job_idempotency_key
from app.application.story_resolution import apply_story_result, refresh_story_resolution_activity
from app.domain.story_jobs import StoryJob, StoryJobOperation, StoryJobStatus
from app.domain.story_resolution import (
    StoryResolutionConflict,
    StoryResolutionOutcome,
    StoryResolutionOwnershipConflict,
    StoryResolutionReceipt,
    StoryResolutionStateConflict,
    build_story_resolution_snapshot,
    story_result_fingerprint,
)


_JOB_COLUMNS = """
    job_id, idempotency_key, operation, room_id, round_number, room_version,
    payload, status, claimed_by, ownership_token, lease_expires_at,
    attempt_count, result, terminal_error
"""


class PostgresStoryResolutionStore(StoryResolutionStore):
    """Same-database coordinator for Room CAS, inbox and completion outbox."""

    def __init__(
        self,
        dsn: str,
        *,
        clock: Clock,
        job_id_factory=None,
        entry_id_factory=None,
        fault_hook=None,
    ) -> None:
        if not dsn:
            raise ValueError("dsn must not be empty")
        self._dsn = dsn
        self._clock = clock
        self._job_id_factory = job_id_factory or (lambda: str(uuid4()))
        self._entry_id_factory = entry_id_factory or (lambda: str(uuid4()))
        self._fault_hook = fault_hook or (lambda point: None)

    def begin_resolution(
        self,
        room_id: str,
        round_number: int,
        expected_version: int,
        skip_pending_spark: bool,
    ) -> StoryJob:
        expected_job_version = expected_version + 1
        key = story_job_idempotency_key(
            StoryJobOperation.RESOLVE_ROUND,
            room_id,
            round_number,
            expected_job_version,
        )
        with psycopg.connect(self._dsn) as connection:
            row = connection.execute(
                f"""
                SELECT {_JOB_COLUMNS}
                FROM story_jobs
                WHERE idempotency_key = %s
                FOR UPDATE
                """,
                (key,),
            ).fetchone()
            if row is not None:
                existing = _job_from_row(row)
                if (
                    existing.operation is not StoryJobOperation.RESOLVE_ROUND
                    or existing.room_id != room_id
                    or existing.round_number != round_number
                    or existing.room_version != expected_job_version
                    or existing.payload.get("producer")
                    != {
                        "source_room_version": expected_version,
                        "skip_pending_spark": skip_pending_spark,
                    }
                ):
                    raise StoryResolutionConflict("producer replay changed input")
                return existing

            room_row = connection.execute(
                "SELECT payload FROM rooms WHERE id = %s FOR UPDATE",
                (room_id,),
            ).fetchone()
            if room_row is None:
                raise StoryResolutionStateConflict("room not found")
            room = _room_from_payload(room_row[0])
            if room.version != expected_version:
                raise StoryResolutionStateConflict("room version conflict")
            if room.round_number != round_number:
                raise StoryResolutionStateConflict("round mismatch")
            if room.status not in {"AWAITING_SPARK", "RESOLVING", "RESOLUTION_FAILED"}:
                raise StoryResolutionStateConflict("room cannot begin resolution")
            results = [
                item for item in room.dice_results if item.round_number == round_number
            ]
            pending = [item for item in results if item.spark_decision == "PENDING"]
            if pending and not skip_pending_spark:
                raise StoryResolutionStateConflict("spark decisions are pending")
            for item in pending:
                item.spark_decision = "DECLINE"
            room.status = "RESOLVING"
            room.version += 1
            payload = build_story_resolution_snapshot(
                room,
                source_room_version=expected_version,
                skip_pending_spark=skip_pending_spark,
            )
            job = create_story_job(
                operation=StoryJobOperation.RESOLVE_ROUND,
                room_id=room.id,
                round_number=round_number,
                room_version=room.version,
                payload=payload,
                job_id=self._job_id_factory(),
            )
            self._fault_hook("after_room_cas")
            connection.execute(
                """
                INSERT INTO story_jobs (
                    job_id, idempotency_key, operation, room_id, round_number,
                    room_version, payload, status, attempt_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', 0)
                """,
                (
                    job.job_id,
                    job.idempotency_key,
                    job.operation.value,
                    job.room_id,
                    job.round_number,
                    job.room_version,
                    Jsonb(deepcopy(job.payload)),
                ),
            )
            self._fault_hook("after_job_insert")
            connection.execute(
                """
                INSERT INTO story_job_dispatch_outbox (job_id, message_payload)
                VALUES (
                    %s,
                    jsonb_build_object('schema_version', 1, 'job_id', %s)
                )
                """,
                (job.job_id, job.job_id),
            )
            self._fault_hook("after_dispatch_insert")
            PostgresRoomRepository._save(connection, room)
            self._fault_hook("after_room_save")
            return job

    def result_for_claim(self, job: StoryJob) -> StoryResolutionReceipt | None:
        with psycopg.connect(self._dsn) as connection:
            current = self._required_active_claim(connection, job)
            row = self._receipt_row(connection, current.job_id)
            if row is None:
                return None
            receipt = _receipt_from_row(row)
            connection.execute(
                """
                UPDATE story_completion_outbox
                SET ownership_token = %s, updated_at = %s
                WHERE job_id = %s AND dispatched_at IS NULL
                """,
                (current.ownership_token, self._utc_now(), current.job_id),
            )
            return receipt

    def commit_result(
        self,
        job: StoryJob,
        result: dict[str, Any],
    ) -> StoryResolutionReceipt:
        now = self._utc_now()
        fingerprint = story_result_fingerprint(result)
        with psycopg.connect(self._dsn) as connection:
            current = self._required_active_claim(connection, job, now=now)
            existing_row = self._receipt_row(connection, current.job_id)
            if existing_row is not None:
                existing = _receipt_from_row(existing_row)
                if existing.result_fingerprint != fingerprint:
                    raise StoryResolutionConflict("result replay diverged")
                connection.execute(
                    """
                    UPDATE story_completion_outbox
                    SET ownership_token = %s, updated_at = %s
                    WHERE job_id = %s AND dispatched_at IS NULL
                    """,
                    (current.ownership_token, now, current.job_id),
                )
                return existing

            room_row = connection.execute(
                "SELECT payload FROM rooms WHERE id = %s FOR UPDATE",
                (job.room_id,),
            ).fetchone()
            if room_row is None:
                raise StoryResolutionStateConflict("room not found")
            room = _room_from_payload(room_row[0])
            if (
                room.version != job.room_version
                or room.round_number != job.round_number
                or room.status != "RESOLVING"
            ):
                outcome = StoryResolutionOutcome.STALE
                room_version_after = None
            else:
                outcome, completed = apply_story_result(
                    room,
                    deepcopy(result),
                    entry_id_factory=self._entry_id_factory,
                    ending_narration_factory=lambda current_room: _required_ending(result),
                )
                refresh_story_resolution_activity(room, now=now, completed=completed)
                room_version_after = room.version
                PostgresRoomRepository._save(connection, room)
                self._fault_hook("after_room_result")

            receipt = StoryResolutionReceipt.create(
                job=current,
                outcome=outcome,
                result=result,
                room_version_after=room_version_after,
            )
            connection.execute(
                """
                INSERT INTO story_result_inbox (
                    job_id, room_id, round_number, room_version,
                    result_fingerprint, result, outcome, room_version_after,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    receipt.job_id,
                    receipt.room_id,
                    receipt.round_number,
                    receipt.room_version,
                    receipt.result_fingerprint,
                    Jsonb(deepcopy(receipt.result)),
                    receipt.outcome.value,
                    receipt.room_version_after,
                    now,
                ),
            )
            self._fault_hook("after_inbox_insert")
            connection.execute(
                """
                INSERT INTO story_completion_outbox (
                    job_id, ownership_token, completion_payload,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    receipt.job_id,
                    current.ownership_token,
                    Jsonb(receipt.completion_result),
                    now,
                    now,
                ),
            )
            self._fault_hook("after_outbox_insert")
            return receipt

    def mark_completion_dispatched(
        self,
        job_id: str,
        ownership_token: str,
    ) -> None:
        now = self._utc_now()
        with psycopg.connect(self._dsn) as connection:
            row = connection.execute(
                """
                UPDATE story_completion_outbox
                SET dispatched_at = COALESCE(dispatched_at, %s), updated_at = %s
                WHERE job_id = %s AND ownership_token = %s
                RETURNING job_id
                """,
                (now, now, job_id, ownership_token),
            ).fetchone()
            if row is None:
                raise StoryResolutionOwnershipConflict("completion token changed")

    def _required_active_claim(
        self,
        connection,
        supplied: StoryJob,
        *,
        now: datetime | None = None,
    ) -> StoryJob:
        checked_at = now or self._utc_now()
        row = connection.execute(
            f"""
            SELECT {_JOB_COLUMNS}
            FROM story_jobs
            WHERE job_id = %s
            FOR UPDATE
            """,
            (supplied.job_id,),
        ).fetchone()
        if row is None:
            raise StoryResolutionStateConflict("job not found")
        current = _job_from_row(row)
        if current.status is not StoryJobStatus.CLAIMED:
            raise StoryResolutionStateConflict("result requires claimed job")
        if (
            current.ownership_token != supplied.ownership_token
            or current.attempt_count != supplied.attempt_count
        ):
            raise StoryResolutionOwnershipConflict("claim was fenced")
        if (
            current.idempotency_key != supplied.idempotency_key
            or current.operation is not supplied.operation
            or current.room_id != supplied.room_id
            or current.round_number != supplied.round_number
            or current.room_version != supplied.room_version
            or current.payload != supplied.payload
            or current.claimed_by != supplied.claimed_by
        ):
            raise StoryResolutionOwnershipConflict("claim identity was changed")
        if current.lease_expires_at is None or checked_at >= current.lease_expires_at:
            raise StoryResolutionOwnershipConflict("claim lease expired")
        return current

    @staticmethod
    def _receipt_row(connection, job_id: str):
        return connection.execute(
            """
            SELECT job_id, room_id, round_number, room_version,
                   result_fingerprint, result, outcome, room_version_after
            FROM story_result_inbox
            WHERE job_id = %s
            FOR UPDATE
            """,
            (job_id,),
        ).fetchone()

    def _utc_now(self) -> datetime:
        now = self._clock.now()
        if now.tzinfo is None or now.utcoffset() != timedelta(0):
            raise ValueError("clock must return aware UTC")
        return now


def _job_from_row(row) -> StoryJob:
    return StoryJob(
        job_id=row[0],
        idempotency_key=row[1],
        operation=StoryJobOperation(row[2]),
        room_id=row[3],
        round_number=row[4],
        room_version=row[5],
        payload=deepcopy(row[6]),
        status=StoryJobStatus(row[7]),
        claimed_by=row[8],
        ownership_token=row[9],
        lease_expires_at=row[10],
        attempt_count=row[11],
        result=deepcopy(row[12]),
        terminal_error=row[13],
    )


def _receipt_from_row(row) -> StoryResolutionReceipt:
    return StoryResolutionReceipt(
        job_id=row[0],
        room_id=row[1],
        round_number=row[2],
        room_version=row[3],
        result_fingerprint=row[4],
        result=deepcopy(row[5]),
        outcome=StoryResolutionOutcome(row[6]),
        room_version_after=row[7],
    )


def _required_ending(result: dict[str, Any]) -> str:
    narration = result.get("ending_narration")
    if not isinstance(narration, str) or not narration:
        raise StoryResolutionStateConflict("final round requires ending narration")
    return narration
