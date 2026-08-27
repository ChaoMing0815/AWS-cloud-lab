# Bounded Support Agent Persistence 驗證摘要

- Scope：`codex/support-agent-persistence`；來源基準 `da6bb28fcd541d0d87e2b468f9a4157829f64419`。
- 安全等級：R3；本批次不接 API、UI、Bedrock、GitHub Issue、Email、外部傳輸。
- R3 validation manifest：
  - app contract：`payload_version`/`requires_human_confirmation`/`submission_status` 固定值驗證；
  - repository contract：同 identity 同內容 replay 需回傳同一草稿；prefix/idempotency 衝突皆 fail closed；
  - migration contract：004 為 append-only 建表與索引，不含 drop/alter；
  - DB contract：不落 raw description / raw identity / 敏感 token；
  - rollback readiness：已啟用 `test_migration_readiness` 當前 schema 檢查包含 `004`；
  - restart contract：`CO_STORY_SUPPORT_TEST_DATABASE_URL` 可用時做 adapter restart replay 測試（環境缺失即 skip，不聲稱 durable）。

- 主要 checkpoints：
  - `backend/tests/test_support_agent_reports.py`
  - `backend/tests/test_postgres_support_report_migration.py`
  - `backend/tests/test_postgres_support_report_repository.py`
  - `backend/tests/test_postgres_support_report_process_e2e.py`
  - `backend/tests/test_migration_readiness.py`

- Blocker（保留於 PR）：backward-compatible migration rollback gate 未解開前不可 merge；需由整合 task 取得後續同意。
