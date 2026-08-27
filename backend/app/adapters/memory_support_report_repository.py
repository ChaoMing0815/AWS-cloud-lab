from app.domain.support_agent import SupportReportConflict
from app.domain.support_agent import ProblemReportDraft


class MemorySupportReportRepository:
    """Local/test adapter only; it does not provide durable persistence."""

    is_durable = False

    def __init__(self) -> None:
        self._drafts_by_key: dict[str, ProblemReportDraft] = {}
        self._drafts_by_id: dict[str, ProblemReportDraft] = {}

    def get_or_save(self, draft: ProblemReportDraft) -> ProblemReportDraft:
        if draft.report_id in self._drafts_by_id:
            existing = self._drafts_by_id[draft.report_id]
            if existing != draft:
                raise SupportReportConflict(
                    "report id collision with divergent payload"
                )
            return existing
        existing = self._drafts_by_key.get(draft.idempotency_key)
        if existing is not None:
            if existing != draft:
                raise SupportReportConflict(
                    "idempotency key collision with divergent payload"
                )
            return existing
        self._drafts_by_key[draft.idempotency_key] = draft
        self._drafts_by_id[draft.report_id] = draft
        return draft

    @property
    def drafts(self) -> tuple[ProblemReportDraft, ...]:
        return tuple(self._drafts_by_key.values())

    @property
    def count(self) -> int:
        return len(self._drafts_by_key)
