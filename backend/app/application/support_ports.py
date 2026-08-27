from typing import Protocol

from app.domain.support_agent import ProblemReportDraft, RuleAnswer, RuleRecord


class SupportModel(Protocol):
    def propose(self, message: str) -> object: ...


class RulesKnowledgeBase(Protocol):
    def lookup(self, query: str) -> RuleAnswer: ...

    def get(self, rule_id: str) -> RuleRecord | None: ...


class SupportReportRepository(Protocol):
    def get_or_save(self, draft: ProblemReportDraft) -> ProblemReportDraft: ...

