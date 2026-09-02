import importlib
import json
from pathlib import Path

import pytest


def _support_types():
    try:
        application = importlib.import_module("app.application.support_agent")
        adapters = importlib.import_module("app.adapters.static_rules_knowledge_base")
        model = importlib.import_module("app.adapters.mock_support_model")
        reports = importlib.import_module("app.adapters.memory_support_report_repository")
    except ModuleNotFoundError:
        pytest.fail("Support Agent Phase A core is not implemented yet")
    return application, adapters, model, reports


def _agent(*, proposal=None):
    application, adapters, model, reports = _support_types()
    knowledge = adapters.StaticRulesKnowledgeBase.from_default_resource()
    support_model = model.MockSupportModel(proposal=proposal)
    repository = reports.MemorySupportReportRepository()
    return application.SupportAgent(
        model=support_model,
        rules_knowledge_base=knowledge,
        report_repository=repository,
    )


def test_lookup_game_rules_returns_canonical_content_and_stable_citation() -> None:
    agent = _agent()

    answer = agent.respond("星火可以怎麼使用？")

    rules_path = Path(__file__).parents[1] / "app" / "resources" / "game_rules.json"
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    spark = next(record for record in rules["rules"] if record["id"] == "spark-usage")
    assert answer.status == "supported"
    assert answer.answer == spark["content"]
    assert len(answer.citations) == 1
    citation = answer.citations[0]
    assert citation.rule_id == "spark-usage"
    assert citation.title == spark["title"]
    assert citation.source_section == "正式 MVP Spec §10 星火"
    assert citation.source_version == rules["version"]


@pytest.mark.parametrize(
    ("rule_id", "queries"),
    [
        (
            "player-count-and-round-limit",
            ("我要怎麼開始遊戲？", "開局需要多少人？"),
        ),
        (
            "character-attributes",
            ("角色的屬性點要如何分配？", "勇氣洞察跟羈絆要怎麼加點？"),
        ),
        (
            "round-flow",
            ("每一輪大家依序要做哪些事情？", "玩家的行動什麼時候會給其他人看到？"),
        ),
        (
            "dice-outcomes",
            ("擲骰之後怎樣才算成功？", "骰到七點會發生什麼結果？"),
        ),
        (
            "spark-usage",
            ("星火拿來做什麼？", "用掉星火會有什麼效果？"),
        ),
        (
            "progress-danger-ending",
            ("進度和危機值會怎麼改變？", "什麼情況會進入不同結局？"),
        ),
    ],
)
def test_common_traditional_chinese_questions_return_one_grounded_rule(
    rule_id: str,
    queries: tuple[str, ...],
) -> None:
    rules_path = Path(__file__).parents[1] / "app" / "resources" / "game_rules.json"
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    expected = next(record for record in rules["rules"] if record["id"] == rule_id)
    agent = _agent()

    for query in queries:
        answer = agent.respond(query)

        assert answer.status == "supported"
        assert answer.answer == expected["content"]
        assert len(answer.citations) == 1
        citation = answer.citations[0]
        assert citation.rule_id == rule_id
        assert citation.title == expected["title"]
        assert citation.source_section == expected["source_section"]
        assert citation.source_version == rules["version"]


@pytest.mark.parametrize(
    ("query", "reason"),
    [
        ("可以交易裝備嗎？", "no_grounded_rule"),
        ("星火可以復活角色嗎？", "no_grounded_rule"),
        ("星火和骰點分別怎麼算？", "ambiguous_rule_query"),
        (
            "我想知道開局人數和角色屬性如何分配？",
            "ambiguous_rule_query",
        ),
    ],
)
def test_lookup_game_rules_fails_closed_without_one_grounded_record(
    query: str,
    reason: str,
) -> None:
    answer = _agent().respond(query)

    assert answer.status == "unsupported"
    assert answer.answer == "目前版本的規則資料沒有足夠證據回答這個問題。"
    assert answer.citations == ()
    assert answer.reason == reason


def test_application_rejects_speculative_text_wrapped_as_unsupported() -> None:
    application, _, model, reports = _support_types()
    domain = importlib.import_module("app.domain.support_agent")

    class MalformedKnowledgeBase:
        def lookup(self, query: str):
            return domain.RuleAnswer(
                status="unsupported",
                answer="星火其實可以復活角色。",
                citations=(),
                reason="no_grounded_rule",
            )

        def get(self, rule_id: str):
            return None

    agent = application.SupportAgent(
        model=model.MockSupportModel(),
        rules_knowledge_base=MalformedKnowledgeBase(),
        report_repository=reports.MemorySupportReportRepository(),
    )

    with pytest.raises(application.SupportAgentRejected) as error:
        agent.respond("星火可以復活角色嗎？")

    assert error.value.code == "ungrounded_knowledge_answer"


def test_static_rule_records_have_complete_versioned_source_metadata() -> None:
    _, adapters, _, _ = _support_types()

    records = adapters.StaticRulesKnowledgeBase.from_default_resource().records

    assert records
    assert len({record.rule_id for record in records}) == len(records)
    for record in records:
        assert record.rule_id
        assert record.title
        assert record.content
        assert record.source_section.startswith("正式 MVP Spec §")
        assert record.source_version
