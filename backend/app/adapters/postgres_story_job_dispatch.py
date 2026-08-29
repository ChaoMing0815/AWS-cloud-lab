from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

import psycopg

from app.application.ports import Clock


class StoryJobDispatchOwnershipConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class StoryJobDispatch:
    job_id: str
    message_payload: dict
    lease_token: str


class PostgresStoryJobDispatchOutbox:
    def __init__(
        self,
        dsn: str,
        *,
        clock: Clock,
        lease_duration: timedelta,
        lease_token_factory: Callable[[], str] | None = None,
    ) -> None:
        if not dsn:
            raise ValueError("dsn must not be empty")
        if lease_duration <= timedelta(0):
            raise ValueError("lease_duration must be positive")
        self._dsn = dsn
        self._clock = clock
        self._lease_duration = lease_duration
        self._lease_token_factory = lease_token_factory or (
            lambda: secrets.token_urlsafe(32)
        )

    def claim_one(self) -> StoryJobDispatch | None:
        now = self._utc_now()
        token = self._lease_token_factory()
        if not token:
            raise ValueError("lease token must not be empty")
        with psycopg.connect(self._dsn) as connection:
            row = connection.execute(
                """
                WITH candidate AS (
                    SELECT job_id
                    FROM story_job_dispatch_outbox
                    WHERE status = 'pending'
                       OR (status = 'publishing' AND lease_expires_at <= %s)
                    ORDER BY created_at, job_id
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE story_job_dispatch_outbox AS dispatch
                SET status = 'publishing',
                    lease_token = %s,
                    lease_expires_at = %s,
                    attempt_count = attempt_count + 1,
                    last_error = NULL,
                    updated_at = %s
                FROM candidate
                WHERE dispatch.job_id = candidate.job_id
                RETURNING dispatch.job_id, dispatch.message_payload
                """,
                (now, token, now + self._lease_duration, now),
            ).fetchone()
        if row is None:
            return None
        return StoryJobDispatch(
            job_id=str(row[0]),
            message_payload=dict(row[1]),
            lease_token=token,
        )

    def mark_dispatched(self, job_id: str, lease_token: str) -> None:
        now = self._utc_now()
        with psycopg.connect(self._dsn) as connection:
            row = connection.execute(
                """
                UPDATE story_job_dispatch_outbox
                SET status = 'dispatched',
                    lease_token = NULL,
                    lease_expires_at = NULL,
                    dispatched_at = %s,
                    updated_at = %s
                WHERE job_id = %s
                  AND status = 'publishing'
                  AND lease_token = %s
                  AND lease_expires_at > %s
                RETURNING job_id
                """,
                (now, now, job_id, lease_token, now),
            ).fetchone()
        if row is None:
            raise StoryJobDispatchOwnershipConflict("dispatch lease changed")

    def release(self, job_id: str, lease_token: str, error_code: str) -> None:
        if not error_code:
            raise ValueError("error_code must not be empty")
        now = self._utc_now()
        with psycopg.connect(self._dsn) as connection:
            row = connection.execute(
                """
                UPDATE story_job_dispatch_outbox
                SET status = 'pending',
                    lease_token = NULL,
                    lease_expires_at = NULL,
                    last_error = %s,
                    updated_at = %s
                WHERE job_id = %s
                  AND status = 'publishing'
                  AND lease_token = %s
                  AND lease_expires_at > %s
                RETURNING job_id
                """,
                (error_code, now, job_id, lease_token, now),
            ).fetchone()
        if row is None:
            raise StoryJobDispatchOwnershipConflict("dispatch lease changed")

    def _utc_now(self) -> datetime:
        now = self._clock.now()
        if now.tzinfo is None or now.utcoffset() != timedelta(0):
            raise ValueError("clock must return aware UTC")
        return now
