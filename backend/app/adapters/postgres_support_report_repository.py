from __future__ import annotations

import psycopg

from app.application.support_ports import SupportReportRepository
from app.application.support_agent import _validate_report
from app.domain.support_agent import ProblemReportDraft, SupportReportConflict


class PostgresSupportReportRepository(SupportReportRepository):
    """Persistent repository for support drafts with idempotent replay contract."""

    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("dsn must not be empty")
        self._dsn = dsn

    def get_or_save(self, draft: ProblemReportDraft) -> ProblemReportDraft:
        _validate_report(draft)
        with psycopg.connect(self._dsn) as connection:
            inserted = connection.execute(
                """
                INSERT INTO support_report_drafts (
                    report_id,
                    payload_version,
                    reporter_identity_hash,
                    content_fingerprint,
                    idempotency_key,
                    category,
                    summary,
                    reproduction_steps,
                    expected_behavior,
                    actual_behavior,
                    requires_human_confirmation,
                    submission_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING report_id, payload_version, reporter_identity_hash, content_fingerprint,
                    idempotency_key, category, summary, reproduction_steps,
                    expected_behavior, actual_behavior,
                    requires_human_confirmation, submission_status
                """,
                _to_db_params(draft),
            ).fetchone()
            if inserted is not None:
                return _validated_from_row(inserted)

            row = connection.execute(
                """
                SELECT report_id, payload_version, reporter_identity_hash, content_fingerprint,
                    idempotency_key, category, summary, reproduction_steps,
                    expected_behavior, actual_behavior,
                    requires_human_confirmation, submission_status
                FROM support_report_drafts
                WHERE idempotency_key = %s OR report_id = %s
                FOR UPDATE
                """,
                (draft.idempotency_key, draft.report_id),
            ).fetchone()
            if row is None:
                raise SupportReportConflict("report identity conflict could not be resolved")
            existing = _validated_from_row(row)
            if existing.idempotency_key == draft.idempotency_key:
                if existing != draft:
                    raise SupportReportConflict("idempotency key reused with divergent payload")
            elif existing.report_id == draft.report_id:
                if existing != draft:
                    raise SupportReportConflict("16-hex prefix collision with divergent payload")
                return existing
            else:
                raise SupportReportConflict("report identity collision")
            return existing


def _to_db_params(draft: ProblemReportDraft) -> tuple[object, ...]:
    return (
        draft.report_id,
        draft.payload_version,
        draft.reporter_identity_hash,
        draft.payload_fingerprint,
        draft.idempotency_key,
        draft.category,
        draft.summary,
        list(draft.reproduction_steps),
        draft.expected_behavior,
        draft.actual_behavior,
        draft.requires_human_confirmation,
        draft.submission_status,
    )


def _from_row(row) -> ProblemReportDraft:
    return ProblemReportDraft(
        report_id=row[0],
        payload_version=row[1],
        reporter_identity_hash=row[2],
        payload_fingerprint=row[3],
        idempotency_key=row[4],
        category=row[5],
        summary=row[6],
        reproduction_steps=tuple(row[7] or ()),
        expected_behavior=row[8],
        actual_behavior=row[9],
        requires_human_confirmation=row[10],
        submission_status=row[11],
    )


def _validated_from_row(row) -> ProblemReportDraft:
    draft = _from_row(row)
    _validate_report(draft)
    return draft
