from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations" / "004_create_support_report_drafts.sql"


def _sql() -> str:
    assert MIGRATION.is_file(), "Support report draft migration 尚未建立"
    return " ".join(MIGRATION.read_text(encoding="utf-8").lower().split())


def test_support_report_migration_is_append_only_and_stable_version_shape() -> None:
    sql = _sql()

    assert "create table support_report_drafts" in sql
    assert "primary key" in sql
    assert "payload_version smallint not null check (payload_version = 1)" in sql
    assert "reporter_identity_hash text not null" in sql
    assert "content_fingerprint text not null" in sql
    assert "idempotency_key text not null unique" in sql
    assert "requires_human_confirmation boolean not null" in sql
    assert "submission_status text not null" in sql
    assert "create index support_report_drafts_lookup_idx" in sql
    assert "alter table" not in sql
    assert "drop table" not in sql


def test_support_report_migration_constrains_payload_shape_and_state_contract() -> None:
    sql = _sql()

    assert "support_report_payload_shape" in sql
    assert "category <> ''" in sql
    assert "summary <> ''" in sql
    assert "expected_behavior <> ''" in sql
    assert "actual_behavior <> ''" in sql
    assert "cardinality(reproduction_steps) between 1 and 20" in sql
    assert "check (reproduction_steps" not in sql or "is not null" in sql
    assert "submission_status = 'local_draft_only'" in sql
    assert "requires_human_confirmation is true" in sql
