import json
from pathlib import Path

from app.domain.support_agent import RuleAnswer, RuleCitation, RuleRecord


_UNSUPPORTED_ANSWER = "目前版本的規則資料沒有足夠證據回答這個問題。"


class StaticRulesKnowledgeBase:
    def __init__(self, records: tuple[RuleRecord, ...]) -> None:
        if not records or len({record.rule_id for record in records}) != len(records):
            raise ValueError("rule records must have unique stable IDs")
        self.records = records
        self._by_id = {record.rule_id: record for record in records}

    @classmethod
    def from_default_resource(cls) -> "StaticRulesKnowledgeBase":
        path = Path(__file__).parents[1] / "resources" / "game_rules.json"
        return cls.from_path(path)

    @classmethod
    def from_path(cls, path: Path) -> "StaticRulesKnowledgeBase":
        document = json.loads(path.read_text(encoding="utf-8"))
        version = _required_text(document, "version")
        raw_rules = document.get("rules")
        if not isinstance(raw_rules, list):
            raise ValueError("rules must be a list")
        records = tuple(
            RuleRecord(
                rule_id=_required_text(raw, "id"),
                title=_required_text(raw, "title"),
                content=_required_text(raw, "content"),
                source_section=_required_text(raw, "source_section"),
                source_version=version,
                keywords=_required_text_list(raw, "keywords"),
                answer_terms=_required_text_list(raw, "answer_terms"),
            )
            for raw in raw_rules
            if isinstance(raw, dict)
        )
        if len(records) != len(raw_rules):
            raise ValueError("each rule must be an object")
        return cls(records)

    def get(self, rule_id: str) -> RuleRecord | None:
        return self._by_id.get(rule_id)

    def lookup(self, query: str) -> RuleAnswer:
        normalized = " ".join(query.casefold().split())
        matches = tuple(
            record
            for record in self.records
            if any(keyword.casefold() in normalized for keyword in record.keywords)
            and any(term.casefold() in normalized for term in record.answer_terms)
        )
        if len(matches) != 1:
            return RuleAnswer(
                status="unsupported",
                answer=_UNSUPPORTED_ANSWER,
                citations=(),
                reason="ambiguous_rule_query" if len(matches) > 1 else "no_grounded_rule",
            )
        record = matches[0]
        return RuleAnswer(
            status="supported",
            answer=record.content,
            citations=(
                RuleCitation(
                    rule_id=record.rule_id,
                    title=record.title,
                    source_section=record.source_section,
                    source_version=record.source_version,
                ),
            ),
        )


def _required_text(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be non-empty text")
    return value.strip()


def _required_text_list(mapping: dict[str, object], key: str) -> tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} must be a non-empty list")
    items = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(items) != len(value):
        raise ValueError(f"{key} must contain non-empty text")
    return items
