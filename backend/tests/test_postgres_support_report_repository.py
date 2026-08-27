from __future__ import annotations

import importlib
import importlib.util
import os
from dataclasses import replace
from types import SimpleNamespace

import pytest

from app.adapters.mock_support_model import MockSupportModel
from app.adapters.static_rules_knowledge_base import StaticRulesKnowledgeBase
from app.application.support_agent import SupportAgent
from app.domain.support_agent import ProblemReportDraft, SupportReportConflict

psycopg = pytest.importorskip("psycopg")


class _Result:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None


class _ScriptedConnection:
    def __init__(self, script):
        self.script = list(script)
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        normalized = " ".join(sql.lower().split())
        assert self.script, f"unexpected SQL: {normalized}"
        expected, rows = self.script.pop(0)
        assert expected in normalized
        return _Result(rows)


def _load_repo_module():
    spec = importlib.util.find_spec("app.adapters.postgres_support_report_repository")
    assert (
        spec is not None
    ), "PostgresSupportReportRepository 尚未建立"
    return importlib.import_module("app.adapters.postgres_support_report_repository")


def _draft(*, report_id="draft-1122334455667788", content="操作失敗", idempotency_key="a" * 64):
    return ProblemReportDraft(
        report_id=report_id,
        payload_version=1,
        reporter_identity_hash="c" * 64,
        payload_fingerprint="f" * 64,
        category="general_issue",
        summary=content,
        reproduction_steps=("重現步驟一",),
        expected_behavior="待人工補充",
        actual_behavior="實際行為",
        requires_human_confirmation=True,
        submission_status="local_draft_only",
        idempotency_key=idempotency_key,
    )


def _row_for(draft: ProblemReportDraft) -> tuple:
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


def _agent(repository) -> SupportAgent:
    return SupportAgent(
        model=MockSupportModel(),
        rules_knowledge_base=StaticRulesKnowledgeBase.from_default_resource(),
        report_repository=repository,
    )


def test_postgres_repository_implements_support_report_contract_without_real_connect() -> None:
    repository_module = _load_repo_module()
    repository = repository_module.PostgresSupportReportRepository("postgresql://test/ignored")

    assert hasattr(repository, "get_or_save")


def test_insert_then_replay_same_draft_within_connection(monkeypatch) -> None:
    module = _load_repo_module()
    primary = _draft()
    connection = _ScriptedConnection(
        [
            ("insert into support_report_drafts", [_row_for(primary)]),
            ("for update", [_row_for(primary)]),
        ]
    )
    monkeypatch.setattr(
        module,
        "psycopg",
        SimpleNamespace(connect=lambda _dsn: connection),
    )

    repository = module.PostgresSupportReportRepository("postgresql://test/ignored")

    assert repository.get_or_save(primary) == primary
    assert repository.get_or_save(primary) == primary
    assert "on conflict do nothing" in " ".join(connection.statements[0][0].lower().split())
    assert "for update" in " ".join(connection.statements[1][0].lower().split())


def test_divergent_replay_raises_support_report_conflict(monkeypatch) -> None:
    module = _load_repo_module()
    original = _draft(summary="原始摘要")
    replay = replace(original, summary="不同摘要")
    connection = _ScriptedConnection(
        [
            ("insert into support_report_drafts", []),
            ("where idempotency_key = %s or report_id = %s", [_row_for(original)]),
        ]
    )
    monkeypatch.setattr(
        module,
        "psycopg",
        SimpleNamespace(connect=lambda _dsn: connection),
    )

    repository = module.PostgresSupportReportRepository("postgresql://test/ignored")

    with pytest.raises(SupportReportConflict, match="idempotency key reused"):
        repository.get_or_save(replay)


def test_support_report_repo_raises_conflict_on_report_id_prefix_collision(monkeypatch) -> None:
    module = _load_repo_module()
    original = _draft(report_id="draft-0000000000000000")
    collision = replace(original, idempotency_key="b" * 64, summary="collision")
    connection = _ScriptedConnection(
        [
            ("insert into support_report_drafts", []),
            ("where idempotency_key = %s or report_id = %s", [_row_for(original)]),
        ]
    )
    monkeypatch.setattr(
        module,
        "psycopg",
        SimpleNamespace(connect=lambda _dsn: connection),
    )

    repository = module.PostgresSupportReportRepository("postgresql://test/ignored")

    with pytest.raises(SupportReportConflict, match="16-hex"):
        repository.get_or_save(collision)


@pytest.mark.skipif(
    "CO_STORY_SUPPORT_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定 support 報表 PostgreSQL 測試 DSN",
)
def test_postgres_support_report_repository_replays_across_instances() -> None:
    dsn = os.environ["CO_STORY_SUPPORT_TEST_DATABASE_URL"]
    psycopg = pytest.importorskip("psycopg")
    repository_module = _load_repo_module()
    migrations = importlib.import_module("app.adapters.postgres_migrations")

    migrations.apply_migrations(dsn)
    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM support_report_drafts")

    first_agent = _agent(repository_module.PostgresSupportReportRepository(dsn))
    second_agent = _agent(repository_module.PostgresSupportReportRepository(dsn))

    first = first_agent.respond("問題回報：跨程序重啟後依舊一致。", reporter_identity="player-local-001")
    second = second_agent.respond(
        "問題回報：跨程序重啟後依舊一致。  ",
        reporter_identity="player-local-001",
    )

    assert first == second
