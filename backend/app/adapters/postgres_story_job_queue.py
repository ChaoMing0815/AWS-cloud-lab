from __future__ import annotations

import secrets
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from app.application.ports import Clock, StoryJobQueue
from app.domain.story_jobs import (
    StoryJob,
    StoryJobConflict,
    StoryJobNotFound,
    StoryJobOperation,
    StoryJobOwnershipConflict,
    StoryJobStateConflict,
    StoryJobStatus,
)


_JOB_COLUMNS = """
    job_id,
    idempotency_key,
    operation,
    room_id,
    round_number,
    room_version,
    payload,
    status,
    claimed_by,
    ownership_token,
    lease_expires_at,
    attempt_count,
    result,
    terminal_error
"""


class PostgresStoryJobQueue(StoryJobQueue):
    """Durable at-least-once queue state with lease and fencing CAS guards."""

    def __init__(
        self,
        dsn: str,
        *,
        clock: Clock,
        lease_duration: timedelta,
        max_attempts: int,
        ownership_token_factory: Callable[[], str] | None = None,
    ) -> None:
        if not dsn:
            raise ValueError("dsn must not be empty")
        if lease_duration <= timedelta(0):
            raise ValueError("lease_duration must be positive")
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        self._dsn = dsn
        self._clock = clock
        self._lease_duration = lease_duration
        self._max_attempts = max_attempts
        self._ownership_token_factory = (
            ownership_token_factory or (lambda: secrets.token_urlsafe(32))
        )

    def enqueue(self, job: StoryJob) -> StoryJob:
        if job.status is not StoryJobStatus.PENDING:
            raise StoryJobStateConflict("only pending jobs can be enqueued")
        with psycopg.connect(self._dsn) as connection:
            inserted = connection.execute(
                f"""
                INSERT INTO story_jobs (
                    job_id, idempotency_key, operation, room_id, round_number,
                    room_version, payload, status, claimed_by, ownership_token,
                    lease_expires_at, attempt_count, result, terminal_error
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING {_JOB_COLUMNS}
                """,
                _job_parameters(job),
            ).fetchone()
            if inserted is not None:
                return _job_from_row(inserted)

            rows = connection.execute(
                f"""
                SELECT {_JOB_COLUMNS}
                FROM story_jobs
                WHERE job_id = %s OR idempotency_key = %s
                FOR UPDATE
                """,
                (job.job_id, job.idempotency_key),
            ).fetchall()
            if not rows:
                raise StoryJobConflict("identity conflict could not be resolved")
            existing = [_job_from_row(row) for row in rows]
            if len(existing) != 1 or existing[0] != job:
                raise StoryJobConflict("job id or idempotency key reused")
            return existing[0]

    def claim(self, job_id: str, worker_id: str) -> StoryJob:
        if not worker_id:
            raise ValueError("worker_id must not be empty")
        now = self._utc_now()
        with psycopg.connect(self._dsn) as connection:
            current = self._required_for_update(connection, job_id)
            if current.status is StoryJobStatus.CLAIMED:
                if current.lease_expires_at is not None and now < current.lease_expires_at:
                    if current.claimed_by != worker_id:
                        raise StoryJobOwnershipConflict("job is owned by another worker")
                    return current
                if current.attempt_count >= self._max_attempts:
                    return self._dead_letter_expired(connection, current, now)
            elif current.status is not StoryJobStatus.PENDING:
                raise StoryJobStateConflict("job cannot be claimed from its current state")

            token = self._new_ownership_token()
            row = connection.execute(
                f"""
                UPDATE story_jobs
                SET status = 'claimed',
                    claimed_by = %s,
                    ownership_token = %s,
                    lease_expires_at = %s,
                    attempt_count = attempt_count + 1,
                    terminal_error = NULL,
                    updated_at = %s
                WHERE job_id = %s
                  AND (
                    status = 'pending'
                    OR (
                        status = 'claimed'
                        AND lease_expires_at <= %s
                        AND attempt_count < %s
                    )
                  )
                RETURNING {_JOB_COLUMNS}
                """,
                (
                    worker_id,
                    token,
                    now + self._lease_duration,
                    now,
                    job_id,
                    now,
                    self._max_attempts,
                ),
            ).fetchone()
            if row is None:
                raise StoryJobStateConflict("claim compare-and-set failed")
            return _job_from_row(row)

    def complete(
        self,
        job_id: str,
        ownership_token: str,
        result: dict[str, Any],
    ) -> StoryJob:
        if not ownership_token:
            raise ValueError("ownership_token must not be empty")
        now = self._utc_now()
        with psycopg.connect(self._dsn) as connection:
            current = self._required_for_update(connection, job_id)
            if current.status is StoryJobStatus.COMPLETED:
                if current.ownership_token == ownership_token and current.result == result:
                    return current
                raise StoryJobConflict("completed job replay changed token or result")
            if current.status is not StoryJobStatus.CLAIMED:
                raise StoryJobStateConflict("job must be claimed before completion")
            self._require_active_token(current, ownership_token, now)
            row = connection.execute(
                f"""
                UPDATE story_jobs
                SET status = 'completed',
                    lease_expires_at = NULL,
                    result = %s,
                    completed_at = %s,
                    updated_at = %s
                WHERE job_id = %s
                  AND status = 'claimed'
                  AND ownership_token = %s
                  AND lease_expires_at > %s
                RETURNING {_JOB_COLUMNS}
                """,
                (Jsonb(deepcopy(result)), now, now, job_id, ownership_token, now),
            ).fetchone()
            if row is None:
                raise StoryJobOwnershipConflict("completion compare-and-set failed")
            return _job_from_row(row)

    def fail(
        self,
        job_id: str,
        ownership_token: str,
        error_code: str,
    ) -> StoryJob:
        if not ownership_token:
            raise ValueError("ownership_token must not be empty")
        if not error_code:
            raise ValueError("error_code must not be empty")
        now = self._utc_now()
        with psycopg.connect(self._dsn) as connection:
            current = self._required_for_update(connection, job_id)
            if current.status is not StoryJobStatus.CLAIMED:
                raise StoryJobStateConflict("only claimed jobs can fail")
            self._require_active_token(current, ownership_token, now)
            exhausted = current.attempt_count >= self._max_attempts
            if exhausted:
                sql = f"""
                    UPDATE story_jobs
                    SET status = 'dead-lettered',
                        claimed_by = NULL,
                        ownership_token = NULL,
                        lease_expires_at = NULL,
                        terminal_error = %s,
                        dead_lettered_at = %s,
                        updated_at = %s
                    WHERE job_id = %s
                      AND status = 'claimed'
                      AND ownership_token = %s
                      AND lease_expires_at > %s
                    RETURNING {_JOB_COLUMNS}
                """
                params = (error_code, now, now, job_id, ownership_token, now)
            else:
                sql = f"""
                    UPDATE story_jobs
                    SET status = 'pending',
                        claimed_by = NULL,
                        ownership_token = NULL,
                        lease_expires_at = NULL,
                        terminal_error = NULL,
                        updated_at = %s
                    WHERE job_id = %s
                      AND status = 'claimed'
                      AND ownership_token = %s
                      AND lease_expires_at > %s
                    RETURNING {_JOB_COLUMNS}
                """
                params = (now, job_id, ownership_token, now)
            row = connection.execute(sql, params).fetchone()
            if row is None:
                raise StoryJobOwnershipConflict("failure compare-and-set failed")
            return _job_from_row(row)

    def _dead_letter_expired(
        self,
        connection,
        current: StoryJob,
        now: datetime,
    ) -> StoryJob:
        row = connection.execute(
            f"""
            UPDATE story_jobs
            SET status = 'dead-lettered',
                claimed_by = NULL,
                ownership_token = NULL,
                lease_expires_at = NULL,
                terminal_error = 'LEASE_EXPIRED',
                dead_lettered_at = %s,
                updated_at = %s
            WHERE job_id = %s
              AND status = 'claimed'
              AND ownership_token = %s
              AND lease_expires_at <= %s
              AND attempt_count >= %s
            RETURNING {_JOB_COLUMNS}
            """,
            (
                now,
                now,
                current.job_id,
                current.ownership_token,
                now,
                self._max_attempts,
            ),
        ).fetchone()
        if row is None:
            raise StoryJobStateConflict("dead-letter compare-and-set failed")
        return _job_from_row(row)

    def _required_for_update(self, connection, job_id: str) -> StoryJob:
        row = connection.execute(
            f"""
            SELECT {_JOB_COLUMNS}
            FROM story_jobs
            WHERE job_id = %s
            FOR UPDATE
            """,
            (job_id,),
        ).fetchone()
        if row is None:
            raise StoryJobNotFound(job_id)
        return _job_from_row(row)

    @staticmethod
    def _require_active_token(
        job: StoryJob,
        ownership_token: str,
        now: datetime,
    ) -> None:
        if job.ownership_token != ownership_token:
            raise StoryJobOwnershipConflict("operation requires current fencing token")
        if job.lease_expires_at is None or now >= job.lease_expires_at:
            raise StoryJobOwnershipConflict("expired fencing token cannot mutate job")

    def _utc_now(self) -> datetime:
        now = self._clock.now()
        if now.tzinfo is None or now.utcoffset() != timedelta(0):
            raise ValueError("clock must return an aware UTC datetime")
        return now

    def _new_ownership_token(self) -> str:
        token = self._ownership_token_factory()
        if not token:
            raise RuntimeError("ownership token factory returned an empty token")
        return token


def _job_parameters(job: StoryJob) -> tuple[Any, ...]:
    return (
        job.job_id,
        job.idempotency_key,
        job.operation.value,
        job.room_id,
        job.round_number,
        job.room_version,
        Jsonb(deepcopy(job.payload)),
        job.status.value,
        job.claimed_by,
        job.ownership_token,
        job.lease_expires_at,
        job.attempt_count,
        Jsonb(deepcopy(job.result)) if job.result is not None else None,
        job.terminal_error,
    )


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
