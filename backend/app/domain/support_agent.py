from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuleRecord:
    rule_id: str
    title: str
    content: str
    source_section: str
    source_version: str
    keywords: tuple[str, ...]
    answer_terms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuleCitation:
    rule_id: str
    title: str
    source_section: str
    source_version: str


@dataclass(frozen=True, slots=True)
class RuleAnswer:
    status: str
    answer: str
    citations: tuple[RuleCitation, ...]
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ProblemReportDraft:
    report_id: str
    reporter_identity_hash: str
    category: str
    summary: str
    reproduction_steps: tuple[str, ...]
    expected_behavior: str
    actual_behavior: str
    requires_human_confirmation: bool
    submission_status: str
    idempotency_key: str
