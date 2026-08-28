from __future__ import annotations

import importlib
import importlib.util
import os
import threading
import time
from dataclasses import replace
from types import SimpleNamespace

import pytest

from app.adapters.mock_support_model import MockSupportModel
from app.adapters.memory_support_report_repository import MemorySupportReportRepository
from app.adapters.static_rules_knowledge_base import StaticRulesKnowledgeBase
from app.application.support_agent import SupportAgent, _compute_payload_fingerprint
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


def _draft(
    *,
    report_id=None,
    summary="操作失敗",
    idempotency_key="a" * 64,
):
    report_id = report_id or f"draft-{idempotency_key[:16]}"
    category = "general_issue"
    reproduction_steps = ("重現步驟一",)
    expected_behavior = "待人工補充"
    actual_behavior = "實際行為"
    return ProblemReportDraft(
        report_id=report_id,
        payload_version=1,
        reporter_identity_hash="c" * 64,
        payload_fingerprint=_compute_payload_fingerprint(
            category=category,
            summary=summary,
            reproduction_steps=reproduction_steps,
            expected_behavior=expected_behavior,
            actual_behavior=actual_behavior,
        ),
        category=category,
        summary=summary,
        reproduction_steps=reproduction_steps,
        expected_behavior=expected_behavior,
        actual_behavior=actual_behavior,
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


def _normalized_draft() -> ProblemReportDraft:
    first = _agent(MemorySupportReportRepository()).respond(
        "問題回報：並行寫入後仍應保留同一份草稿。",
        reporter_identity="player-local-concurrency",
    )
    second = _agent(MemorySupportReportRepository()).respond(
        "問題回報：並行寫入後仍應保留同一份草稿。  ",
        reporter_identity="player-local-concurrency",
    )

    assert isinstance(first, ProblemReportDraft)
    assert first == second
    return first


def _prepare_durable_database(dsn: str) -> None:
    migrations = importlib.import_module("app.adapters.postgres_migrations")
    migrations.apply_migrations(dsn)
    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM support_report_drafts")


def _concurrently_save(module, monkeypatch, dsn: str, drafts):
    """Run two repository writers through the same real pre-INSERT race point."""

    original_connect = psycopg.connect
    entry_barrier = threading.Barrier(2)
    insert_barrier = threading.Barrier(2)
    lock = threading.Lock()
    backend_pids: set[int] = set()
    insert_intervals: list[tuple[float, float]] = []

    class _DropDelayColumn:
        def __init__(self, result) -> None:
            self._result = result

        def fetchone(self):
            row = self._result.fetchone()
            return None if row is None else row[1:]

    class _BarrierConnection:
        def __init__(self, connection) -> None:
            self._connection = connection

        def __enter__(self):
            self._connection.__enter__()
            return self

        def __exit__(self, exc_type, exc, traceback):
            return self._connection.__exit__(exc_type, exc, traceback)

        def execute(self, sql, params=None):
            normalized = " ".join(sql.lower().split())
            if "insert into support_report_drafts" not in normalized:
                return self._connection.execute(sql, params)

            with lock:
                backend_pids.add(self._connection.info.backend_pid)
            insert_barrier.wait(timeout=5)

            # Keep the winning INSERT transaction open in PostgreSQL.  The
            # competing ON CONFLICT statement must then execute concurrently
            # and wait on the real unique-index race, rather than on a mock.
            delayed_sql = sql.replace(
                "RETURNING report_id,",
                "RETURNING pg_sleep(0.20), report_id,",
                1,
            )
            started_at = time.monotonic()
            try:
                return _DropDelayColumn(self._connection.execute(delayed_sql, params))
            finally:
                with lock:
                    insert_intervals.append((started_at, time.monotonic()))

    def connect(_dsn: str):
        return _BarrierConnection(original_connect(_dsn))

    monkeypatch.setattr(module, "psycopg", SimpleNamespace(connect=connect))
    try:
        results = [None, None]
        errors = [None, None]

        def writer(index: int) -> None:
            try:
                entry_barrier.wait(timeout=5)
                results[index] = module.PostgresSupportReportRepository(dsn).get_or_save(
                    drafts[index]
                )
            except BaseException as error:  # pragma: no cover - asserted below
                errors[index] = error

        writers = [threading.Thread(target=writer, args=(index,)) for index in range(2)]
        for writer_thread in writers:
            writer_thread.start()
        for writer_thread in writers:
            writer_thread.join(timeout=10)

        assert not any(writer_thread.is_alive() for writer_thread in writers)
        assert len(backend_pids) == 2
        assert len(insert_intervals) == 2
        assert max(started_at for started_at, _ in insert_intervals) < min(
            finished_at for _, finished_at in insert_intervals
        )
        return results, errors
    finally:
        monkeypatch.undo()


def _assert_single_canonical_row(dsn: str, canonical: ProblemReportDraft) -> None:
    with psycopg.connect(dsn) as connection:
        rows = connection.execute(
            """
            SELECT report_id, idempotency_key, content_fingerprint,
                requires_human_confirmation, submission_status
            FROM support_report_drafts
            """
        ).fetchall()
        constraints = connection.execute(
            """
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'support_report_drafts'::regclass
            """
        ).fetchall()

    assert rows == [
        (
            canonical.report_id,
            canonical.idempotency_key,
            canonical.payload_fingerprint,
            True,
            "local_draft_only",
        )
    ]
    constraint_definitions = {name: definition for name, definition in constraints}
    assert "support_report_drafts_pkey" in constraint_definitions
    assert "support_report_identity_shape" in constraint_definitions
    assert "support_report_payload_shape" in constraint_definitions
    identity_shape = constraint_definitions["support_report_identity_shape"].replace(
        '"', ""
    )
    assert "left(idempotency_key, 16)" in identity_shape


def test_postgres_repository_implements_support_report_contract_without_real_connect() -> None:
    repository_module = _load_repo_module()
    repository = repository_module.PostgresSupportReportRepository("postgresql://test/ignored")

    assert hasattr(repository, "get_or_save")


def test_insert_then_replay_same_draft_within_connection(monkeypatch) -> None:
    module = _load_repo_module()
    primary = _draft()
    connection = _ScriptedConnection(
        [
            ("insert into support_report_drafts", []),
            ("for update", [_row_for(primary)]),
            ("insert into support_report_drafts", []),
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
    replay = _draft(summary="不同摘要", idempotency_key=original.idempotency_key)
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
    original = _draft(idempotency_key="0" * 64)
    collision = _draft(
        idempotency_key="0" * 16 + "b" * 48,
        summary="collision",
    )
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


def test_postgres_repository_rejects_invalid_draft_before_connecting(monkeypatch) -> None:
    module = _load_repo_module()
    invalid = replace(_draft(), requires_human_confirmation=False)

    def must_not_connect(_dsn):
        raise AssertionError("invalid draft must be rejected before database connection")

    monkeypatch.setattr(module, "psycopg", SimpleNamespace(connect=must_not_connect))
    repository = module.PostgresSupportReportRepository("postgresql://test/ignored")

    with pytest.raises(SupportReportConflict, match="invalid report state"):
        repository.get_or_save(invalid)


def test_postgres_repository_rejects_sensitive_field_before_connecting(monkeypatch) -> None:
    module = _load_repo_module()
    summary = "password=FAKE_PREWRITE_SECRET"
    invalid = _draft(summary=summary)

    def must_not_connect(_dsn):
        raise AssertionError("sensitive draft must be rejected before database connection")

    monkeypatch.setattr(module, "psycopg", SimpleNamespace(connect=must_not_connect))
    repository = module.PostgresSupportReportRepository("postgresql://test/ignored")

    with pytest.raises(SupportReportConflict, match="sensitive data"):
        repository.get_or_save(invalid)


def test_postgres_repository_rejects_corrupt_database_row(monkeypatch) -> None:
    module = _load_repo_module()
    draft = _draft()
    corrupt_row = list(_row_for(draft))
    corrupt_row[10] = False
    connection = _ScriptedConnection(
        [
            ("insert into support_report_drafts", [tuple(corrupt_row)]),
        ]
    )
    monkeypatch.setattr(
        module,
        "psycopg",
        SimpleNamespace(connect=lambda _dsn: connection),
    )
    repository = module.PostgresSupportReportRepository("postgresql://test/ignored")

    with pytest.raises(SupportReportConflict, match="invalid report state"):
        repository.get_or_save(draft)


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


@pytest.mark.skipif(
    "CO_STORY_SUPPORT_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定 support 報表 PostgreSQL 測試 DSN",
)
def test_postgres_repository_concurrent_normalized_drafts_keep_one_canonical_row(
    monkeypatch,
) -> None:
    dsn = os.environ["CO_STORY_SUPPORT_TEST_DATABASE_URL"]
    module = _load_repo_module()
    _prepare_durable_database(dsn)
    draft = _normalized_draft()

    results, errors = _concurrently_save(module, monkeypatch, dsn, (draft, draft))

    assert errors == [None, None]
    assert results == [draft, draft]
    _assert_single_canonical_row(dsn, draft)
    assert module.PostgresSupportReportRepository(dsn).get_or_save(draft) == draft


@pytest.mark.skipif(
    "CO_STORY_SUPPORT_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定 support 報表 PostgreSQL 測試 DSN",
)
def test_postgres_repository_concurrent_divergent_idempotency_key_fails_closed(
    monkeypatch,
) -> None:
    dsn = os.environ["CO_STORY_SUPPORT_TEST_DATABASE_URL"]
    module = _load_repo_module()
    _prepare_durable_database(dsn)
    canonical = _draft(summary="並行 idempotency canonical")
    divergent = _draft(
        summary="並行 idempotency divergent",
        idempotency_key=canonical.idempotency_key,
    )

    results, errors = _concurrently_save(
        module,
        monkeypatch,
        dsn,
        (canonical, divergent),
    )

    successful = [result for result in results if result is not None]
    conflicts = [error for error in errors if error is not None]
    assert len(successful) == 1
    assert len(conflicts) == 1
    assert isinstance(conflicts[0], SupportReportConflict)
    assert "idempotency key reused" in str(conflicts[0])
    stored = successful[0]
    _assert_single_canonical_row(dsn, stored)
    restarted = module.PostgresSupportReportRepository(dsn)
    assert restarted.get_or_save(stored) == stored
    with pytest.raises(SupportReportConflict, match="idempotency key reused"):
        restarted.get_or_save(divergent if stored == canonical else canonical)


@pytest.mark.skipif(
    "CO_STORY_SUPPORT_TEST_DATABASE_URL" not in os.environ,
    reason="需要明確指定 support 報表 PostgreSQL 測試 DSN",
)
def test_postgres_repository_concurrent_report_id_prefix_collision_fails_closed(
    monkeypatch,
) -> None:
    dsn = os.environ["CO_STORY_SUPPORT_TEST_DATABASE_URL"]
    module = _load_repo_module()
    _prepare_durable_database(dsn)
    canonical = _draft(
        summary="並行 report id canonical",
        idempotency_key="f" * 16 + "a" * 48,
    )
    collision = _draft(
        summary="並行 report id collision",
        idempotency_key="f" * 16 + "b" * 48,
    )

    results, errors = _concurrently_save(
        module,
        monkeypatch,
        dsn,
        (canonical, collision),
    )

    successful = [result for result in results if result is not None]
    conflicts = [error for error in errors if error is not None]
    assert len(successful) == 1
    assert len(conflicts) == 1
    assert isinstance(conflicts[0], SupportReportConflict)
    assert "16-hex prefix collision" in str(conflicts[0])
    stored = successful[0]
    _assert_single_canonical_row(dsn, stored)
    restarted = module.PostgresSupportReportRepository(dsn)
    assert restarted.get_or_save(stored) == stored
    with pytest.raises(SupportReportConflict, match="16-hex prefix collision"):
        restarted.get_or_save(collision if stored == canonical else canonical)
