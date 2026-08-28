# Bounded Support Agent Persistence 驗證摘要

- Scope：`codex/support-agent-persistence`；來源基準 `da6bb28fcd541d0d87e2b468f9a4157829f64419`。
- 安全等級：R3；本批次不接 API、UI、Bedrock、GitHub Issue、Email、外部傳輸。
- R3 validation manifest：
  - app contract：repository 前／回傳後以 shared pure validator 驗證固定 state、完整小寫 hash、report ID mapping、payload fingerprint 與已去敏結構欄位；
  - repository contract：同 identity 同內容 replay 需回傳同一草稿；prefix/idempotency 衝突皆 fail closed；DB identity `CHECK` 與 adapter 回傳列 validator 固定 report ID mapping 及 corrupt-row guard；
  - migration contract：004 為 append-only 建表與索引，不含 drop/alter；steps 以 PostgreSQL 合法 array constraint 檢查非空與非 NULL／空元素，沒有 subquery 或步數上限；
  - DB contract：不落 raw description / raw identity / 敏感 token；
  - rollback readiness：已啟用 `test_migration_readiness` 當前 schema 檢查包含 `004`；
  - restart contract：`CO_STORY_SUPPORT_TEST_DATABASE_URL` 可用時做 adapter restart replay 測試（環境缺失即 skip，不聲稱 durable）；目前沒有真實 PostgreSQL restart evidence。

- 主要 checkpoints：
  - `backend/tests/test_support_agent_reports.py`
  - `backend/tests/test_postgres_support_report_migration.py`
  - `backend/tests/test_postgres_support_report_repository.py`
  - `backend/tests/test_postgres_support_report_process_e2e.py`
  - `backend/tests/test_migration_readiness.py`

- Corrective TDD：原整合 Red 為 8 個 assertion failures；主 task review 另以 2 個 Red 固定 DB report ID mapping 與 INSERT corrupt-row guard，最小 Green 後皆通過。
- 最終 targeted：77 passed、2 skipped；兩個 skip 都只因未設定 `CO_STORY_SUPPORT_TEST_DATABASE_URL`。
- Affected migration／bridge／composition／Worker gate：200 passed、1 environment skip。
- 完整 regression：Backend 657 passed、13 skipped；Frontend 96 passed、0 failed；`bash -n ops/release/deploy_container.sh` 通過。
- 代表性 sensitivity：在測試程序內暫時旁路 pre-write validator、INSERT-row validator、application post-validation，並以臨時 004 copy 削弱 identity／unique／human-state constraints；測試均偵測 mutation，mutation 已立即還原。
- `git diff --check` 通過；共同基準上的 pre-merge branch 與 merge-aware branch-owned path boundary 均為 `passed:paths=14`，且 exact `origin/main` 是 merge HEAD ancestor。最終 commit 後仍需以 PR base 重跑 checker；本 manifest 不把 memory tests 或缺 DSN 的 skip 宣稱為 durable/restart 證據。

- Post-merge durability gate（2026-08-28）：以一次性`postgres:16-alpine`、localhost隨機port、無volume的隔離資料庫，同時設定三個專用test DSN；Support repository／process、StoryJob queue、Story Result inbox／outbox與Tier 2 Web／Worker process suites共`33 passed`、無skip。容器完成後已移除，未使用production RDS或AWS。
- 此gate證明adapter／process restart與duplicate-delivery replay；現有suite沒有兩個真實並行writer同時提交Support draft的案例，因此不得宣稱parallel-write durability，需另以strict TDD補足。
- 狀態：migration bridge 已驗證 active，但 production schema 尚未 activation。
- 未接範圍：仍無 API／UI／Bedrock／submit／production wiring。
- 原 backward-compatible old-image rollback blocker 已由 verified active migration bridge 解開；本 PR 在更新後完整 CI 全綠及整合 task 明確判定前仍不得 merge。Production schema activation 另需授權，且本批沒有真實 PostgreSQL restart evidence。
