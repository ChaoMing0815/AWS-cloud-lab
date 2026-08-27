import importlib

import pytest
from dataclasses import replace


def _support_types():
    try:
        application = importlib.import_module("app.application.support_agent")
        adapters = importlib.import_module("app.adapters.static_rules_knowledge_base")
        model = importlib.import_module("app.adapters.mock_support_model")
        reports = importlib.import_module("app.adapters.memory_support_report_repository")
    except ModuleNotFoundError:
        pytest.fail("Support Agent Phase A core is not implemented yet")
    return application, adapters, model, reports


def _agent(*, repository=None, proposal=None):
    application, adapters, model, reports = _support_types()
    repository = repository or reports.MemorySupportReportRepository()
    return (
        application.SupportAgent(
            model=model.MockSupportModel(proposal=proposal),
            rules_knowledge_base=adapters.StaticRulesKnowledgeBase.from_default_resource(),
            report_repository=repository,
        ),
        repository,
    )


def test_draft_problem_report_is_structured_and_requires_human_confirmation() -> None:
    description = """問題回報
分類：gameplay_bug
摘要：星火按鈕在骰點公開後無法操作
重現步驟：
1. 進入等待星火階段
2. 點選使用星火
期望：星火成功套用並更新結果
實際：按鈕沒有反應
"""
    agent, repository = _agent()

    draft = agent.respond(description, reporter_identity="player-local-001")

    assert draft.category == "gameplay_bug"
    assert draft.summary == "星火按鈕在骰點公開後無法操作"
    assert draft.reproduction_steps == ("進入等待星火階段", "點選使用星火")
    assert draft.expected_behavior == "星火成功套用並更新結果"
    assert draft.actual_behavior == "按鈕沒有反應"
    assert draft.requires_human_confirmation is True
    assert draft.submission_status == "local_draft_only"
    assert draft.payload_version == 1
    assert len(draft.payload_fingerprint) == 64
    assert len(draft.idempotency_key) == 64
    assert repository.count == 1


def test_report_replay_is_idempotent_for_same_identity_and_normalized_content() -> None:
    _, _, _, reports = _support_types()
    repository = reports.MemorySupportReportRepository()
    first_agent, _ = _agent(repository=repository)
    replay_agent, _ = _agent(repository=repository)
    description = "問題回報：進入房間後畫面沒有更新。"

    first = first_agent.respond(description, reporter_identity="player-local-001")
    replay = replay_agent.respond(
        "  問題回報：進入房間後畫面沒有更新。  ",
        reporter_identity="player-local-001",
    )
    another_identity = replay_agent.respond(
        description,
        reporter_identity="player-local-002",
    )

    assert replay == first
    assert another_identity.report_id != first.report_id
    assert repository.count == 2
    assert repository.is_durable is False


def test_application_detects_corrupt_persisted_draft_before_return() -> None:
    application, _, _, reports = _support_types()

    class MutatingRepository(reports.MemorySupportReportRepository):
        def __init__(self) -> None:
            super().__init__()
            self._mutate = True

        def get_or_save(self, draft):
            persisted = super().get_or_save(draft)
            if self._mutate:
                self._mutate = False
                return replace(
                    persisted,
                    summary="外部更改過的摘要",
                )
            return persisted

    repository = MutatingRepository()
    agent, _ = _agent(repository=repository)
    with pytest.raises(application.SupportAgentRejected) as error:
        agent.respond("問題回報：操作失敗。", reporter_identity="player-local-001")
    assert error.value.code == "corrupt_report_contract"


def test_draft_report_contains_stable_16_hex_prefix_for_report_id() -> None:
    agent, _ = _agent()
    draft = agent.respond("問題回報：進入房間後畫面沒有更新。", reporter_identity="player-local-001")

    assert draft.report_id.startswith("draft-")
    assert len(draft.report_id) == 22


@pytest.mark.parametrize(
    "sensitive_fragment",
    [
        "Cookie: session_token=FAKE_SESSION_MARKER",
        "Cookie: benign=1; session_token=FAKE_COOKIE_CHAIN_MARKER",
        "session_token=FAKE_STANDALONE_SESSION_MARKER",
        "X-CSRF-Token: FAKE_CSRF_MARKER",
        "password=FAKE_PASSWORD_MARKER",
        "AWS_ACCESS_KEY_ID=AKIAFAKEFAKEFAKEFAKE",
        "DATABASE_URL=postgresql://fake:FAKE_DB_MARKER@localhost/game",
        "RUNTIME_SECRET=FAKE_RUNTIME_MARKER",
        "Authorization: Bearer FAKE_BEARER_MARKER",
    ],
)
def test_report_draft_redacts_sensitive_data_before_persistence(
    sensitive_fragment: str,
) -> None:
    description = f"問題回報：加入房間失敗。除錯內容 {sensitive_fragment}，實際顯示連線錯誤。"
    agent, repository = _agent()

    draft = agent.respond(description, reporter_identity="player-local-001")
    persisted = repository.drafts[0]

    serialized = " ".join(
        (
            draft.summary,
            *draft.reproduction_steps,
            draft.expected_behavior,
            draft.actual_behavior,
            persisted.summary,
            persisted.actual_behavior,
        )
    )
    assert "FAKE_" not in serialized
    assert "AKIA" not in serialized
    assert "postgresql://" not in serialized
    assert "[REDACTED]" in serialized


def test_sensitive_report_input_is_redacted_before_model_proposal() -> None:
    application, adapters, model, reports = _support_types()
    support_model = model.MockSupportModel()
    agent = application.SupportAgent(
        model=support_model,
        rules_knowledge_base=adapters.StaticRulesKnowledgeBase.from_default_resource(),
        report_repository=reports.MemorySupportReportRepository(),
    )

    agent.respond(
        "問題回報：畫面錯誤，password=FAKE_PASSWORD_MARKER",
        reporter_identity="player-local-001",
    )

    assert support_model.received_messages == (
        "問題回報：畫面錯誤，password=[REDACTED]",
    )
