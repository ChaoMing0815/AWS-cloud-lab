import hashlib
import re

from app.application.support_ports import (
    RulesKnowledgeBase,
    SupportModel,
    SupportReportRepository,
)
from app.domain.support_agent import ProblemReportDraft, RuleAnswer


_TOOL_ARGUMENTS = {
    "lookup_game_rules": frozenset({"query"}),
    "draft_problem_report": frozenset({"description"}),
}
_UNSAFE_INSTRUCTIONS = (
    "忽略先前",
    "忽略規則",
    "改寫規則",
    "重寫規則",
    "system prompt",
    "ignore previous",
    "rewrite the",
)
_LABELED_SECRET_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(cookie\s*:\s*)[^\s,，;；]+",
        r"(x-csrf-token\s*:\s*)[^\s,，;；]+",
        r"(csrf(?:_token)?\s*[=:]\s*)[^\s,，;；]+",
        r"(password\s*[=:]\s*)[^\s,，;；]+",
        r"(aws_(?:access_key_id|secret_access_key|session_token)\s*[=:]\s*)[^\s,，;；]+",
        r"(database_url\s*[=:]\s*)[^\s,，;；]+",
        r"((?:runtime_)?secret(?:_key)?\s*[=:]\s*)[^\s,，;；]+",
        r"(authorization\s*:\s*bearer\s+)[^\s,，;；]+",
    )
)
_CREDENTIAL_SHAPES = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"AKIA[A-Z0-9]{16}",
        r"postgres(?:ql)?://[^\s,，;；]+",
        r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    )
)


class SupportAgentRejected(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class SupportAgent:
    def __init__(
        self,
        *,
        model: SupportModel,
        rules_knowledge_base: RulesKnowledgeBase,
        report_repository: SupportReportRepository,
    ) -> None:
        self._model = model
        self._rules = rules_knowledge_base
        self._reports = report_repository

    def respond(
        self,
        message: str,
        *,
        reporter_identity: str | None = None,
    ) -> RuleAnswer | ProblemReportDraft:
        raw_message = message.strip()
        if not _normalize_text(raw_message):
            raise SupportAgentRejected("empty_message")
        if _contains_unsafe_instruction(raw_message):
            raise SupportAgentRejected("unsafe_instruction")
        original_message = _redact_sensitive_data(raw_message)

        tool, arguments = self._validate_proposal(
            self._model.propose(original_message),
            original_message,
        )
        if tool == "lookup_game_rules":
            answer = self._rules.lookup(arguments["query"])
            self._validate_grounded_answer(answer)
            return answer
        if reporter_identity is None or not reporter_identity.strip():
            raise SupportAgentRejected("reporter_identity_required")
        return self._draft_report(
            arguments["description"],
            reporter_identity=reporter_identity,
        )

    def _validate_proposal(
        self,
        proposal: object,
        original_message: str,
    ) -> tuple[str, dict[str, str]]:
        if type(proposal) is not dict or set(proposal) != {"tool", "arguments"}:
            raise SupportAgentRejected("malformed_model_output")
        tool = proposal.get("tool")
        arguments = proposal.get("arguments")
        if not isinstance(tool, str) or tool not in _TOOL_ARGUMENTS:
            raise SupportAgentRejected("tool_not_allowed")
        if type(arguments) is not dict or set(arguments) != _TOOL_ARGUMENTS[tool]:
            raise SupportAgentRejected("invalid_tool_arguments")
        argument_name = next(iter(_TOOL_ARGUMENTS[tool]))
        value = arguments.get(argument_name)
        if not isinstance(value, str) or _normalize_text(value) != _normalize_text(original_message):
            raise SupportAgentRejected("invalid_tool_arguments")
        return tool, {argument_name: original_message}

    def _validate_grounded_answer(self, answer: RuleAnswer) -> None:
        if answer.status == "unsupported":
            if answer.citations:
                raise SupportAgentRejected("ungrounded_knowledge_answer")
            return
        if answer.status != "supported" or len(answer.citations) != 1:
            raise SupportAgentRejected("ungrounded_knowledge_answer")
        citation = answer.citations[0]
        record = self._rules.get(citation.rule_id)
        if (
            record is None
            or answer.answer != record.content
            or citation.title != record.title
            or citation.source_section != record.source_section
            or citation.source_version != record.source_version
        ):
            raise SupportAgentRejected("ungrounded_knowledge_answer")

    def _draft_report(
        self,
        description: str,
        *,
        reporter_identity: str,
    ) -> ProblemReportDraft:
        sanitized = _redact_sensitive_data(description)
        fields = _parse_report_fields(sanitized)
        identity_hash = _sha256(_normalize_text(reporter_identity).casefold())
        content_key = _sha256(_normalize_text(sanitized))
        idempotency_key = _sha256(f"{identity_hash}:{content_key}")
        draft = ProblemReportDraft(
            report_id=f"draft-{idempotency_key[:16]}",
            reporter_identity_hash=identity_hash,
            category=fields["category"],
            summary=fields["summary"],
            reproduction_steps=tuple(fields["reproduction_steps"]),
            expected_behavior=fields["expected_behavior"],
            actual_behavior=fields["actual_behavior"],
            requires_human_confirmation=True,
            submission_status="local_draft_only",
            idempotency_key=idempotency_key,
        )
        return self._reports.get_or_save(draft)


def _contains_unsafe_instruction(message: str) -> bool:
    lowered = message.casefold()
    return any(marker in lowered for marker in _UNSAFE_INSTRUCTIONS)


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def _redact_sensitive_data(value: str) -> str:
    redacted = value
    for pattern in _LABELED_SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
    for pattern in _CREDENTIAL_SHAPES:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _parse_report_fields(description: str) -> dict[str, str | list[str]]:
    fields: dict[str, str | list[str]] = {
        "category": "general_issue",
        "summary": "",
        "reproduction_steps": [],
        "expected_behavior": "待人工補充",
        "actual_behavior": "",
    }
    collecting_steps = False
    for raw_line in description.splitlines():
        line = raw_line.strip()
        if not line or line == "問題回報":
            continue
        if line.startswith("分類："):
            fields["category"] = line.removeprefix("分類：").strip() or "general_issue"
            collecting_steps = False
        elif line.startswith("摘要："):
            fields["summary"] = line.removeprefix("摘要：").strip()
            collecting_steps = False
        elif line.startswith("重現步驟："):
            collecting_steps = True
            inline = line.removeprefix("重現步驟：").strip()
            if inline:
                fields["reproduction_steps"] = [inline]
        elif line.startswith("期望："):
            fields["expected_behavior"] = line.removeprefix("期望：").strip() or "待人工補充"
            collecting_steps = False
        elif line.startswith("實際："):
            fields["actual_behavior"] = line.removeprefix("實際：").strip()
            collecting_steps = False
        elif collecting_steps:
            step = re.sub(r"^\d+[.)、]\s*", "", line)
            if step:
                steps = fields["reproduction_steps"]
                assert isinstance(steps, list)
                steps.append(step)

    normalized_description = _normalize_text(description)
    if not fields["summary"]:
        fields["summary"] = normalized_description.removeprefix("問題回報：").strip()
    if not fields["reproduction_steps"]:
        fields["reproduction_steps"] = ("依使用者描述重現問題",)
    if not fields["actual_behavior"]:
        fields["actual_behavior"] = normalized_description
    return fields


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
