from app.domain.support_agent import ProblemReportDraft


class MemorySupportReportRepository:
    """Local/test adapter only; it does not provide durable persistence."""

    is_durable = False

    def __init__(self) -> None:
        self._drafts_by_key: dict[str, ProblemReportDraft] = {}

    def get_or_save(self, draft: ProblemReportDraft) -> ProblemReportDraft:
        existing = self._drafts_by_key.get(draft.idempotency_key)
        if existing is not None:
            return existing
        self._drafts_by_key[draft.idempotency_key] = draft
        return draft

    @property
    def drafts(self) -> tuple[ProblemReportDraft, ...]:
        return tuple(self._drafts_by_key.values())

    @property
    def count(self) -> int:
        return len(self._drafts_by_key)

