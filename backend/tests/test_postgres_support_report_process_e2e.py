import os

import importlib
import pytest

from app.adapters.mock_support_model import MockSupportModel
from app.adapters.static_rules_knowledge_base import StaticRulesKnowledgeBase
from app.application.support_agent import SupportAgent


@pytest.mark.skipif(
    "CO_STORY_SUPPORT_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定 support 報表 process 測試 DSN",
)
def test_support_report_persistence_survives_adapter_restart_without_duplicate_write() -> None:
    dsn = os.environ["CO_STORY_SUPPORT_TEST_DATABASE_URL"]
    psycopg = pytest.importorskip("psycopg")
    migrations = importlib.import_module("app.adapters.postgres_migrations")
    repository_module = importlib.import_module("app.adapters.postgres_support_report_repository")

    migrations.apply_migrations(dsn)
    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM support_report_drafts")

    first_repo = repository_module.PostgresSupportReportRepository(dsn)
    second_repo = repository_module.PostgresSupportReportRepository(dsn)

    common_rules = StaticRulesKnowledgeBase.from_default_resource()
    first = SupportAgent(
        model=MockSupportModel(),
        rules_knowledge_base=common_rules,
        report_repository=first_repo,
    )
    second = SupportAgent(
        model=MockSupportModel(),
        rules_knowledge_base=common_rules,
        report_repository=second_repo,
    )

    first_draft = first.respond(
        "問題回報：跨程序重啟後依舊一致。", reporter_identity="player-local-001"
    )
    second_draft = second.respond(
        "問題回報：跨程序重啟後依舊一致。  ",
        reporter_identity="player-local-001",
    )

    assert first_draft == second_draft
