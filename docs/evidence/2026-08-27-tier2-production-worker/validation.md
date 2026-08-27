# Tier 2 Production Worker Validation

- 日期：2026-08-27
- Branch：`codex/tier2-production-worker`
- 起始治理主幹：`da6bb28fcd541d0d87e2b468f9a4157829f64419`
- 目標：以 strict TDD 接 production worker 到 existing Bedrock storyteller，維持 Web process 不啟動 Worker、local/test 僅用 mock。

## TDD 紀錄

### Red（`d1b8c33`）

- `backend/tests/test_bedrock_storyteller.py`
  - 以 `resolve_round_and_ending` 的 composite contract 做行為缺口檢查。
  - 在目前程式尚未提供 composite narrator contract 時明確以 assertion 失敗。
- `backend/tests/test_tier2_production_worker.py`
  - 建立 production bootstrap、factory 可載入、runner 隔離與 invocation 約束的 assertion 斷言。
  - 在尚未引入 `production_storyteller_factory` 時以 assertion 失敗。

### Green（`2012859`）

- 增加 production worker entrypoint 與 storyteller factory。
- 本地端/測試端保留 `MockStoryteller`，只在 `CO_STORY_ENV=production` 建立 production runner。
- 非終局與終局分別只對應一筆 `converse`，終局使用同一次 composite 輸出 round+ending。
- `production` 缺失/不合法設定在 bootstrap 或 runtime 前 fail closed。

## Regression

- Targeted tests：
  - `backend/tests/test_bedrock_storyteller.py`
  - `backend/tests/test_tier2_production_worker.py`
  - `backend/tests/test_tier2_async_worker.py`
  - `backend/tests/test_tier2_async_process_e2e.py`
  - `backend/tests/test_production_composition.py`
  - `backend/tests/test_story_job_domain.py`
  - `backend/tests/test_story_job_queue.py`
  - `backend/tests/test_postgres_story_job_queue.py`
  - `backend/tests/test_postgres_story_job_migration.py`
  - `backend/tests/test_story_resolution_workflow.py`
  - `backend/tests/test_story_resolution_characterization.py`
  - `backend/tests/test_story_resolution_domain.py`
  - `backend/tests/test_postgres_story_resolution_store.py`
  - `backend/tests/test_postgres_story_resolution_migration.py`

  結果：`145 passed, 3 skipped`

- Backend full regression：
  - `573 passed, 11 skipped`
- Frontend regression：
  - `96 passed, 0 failed`

## 安全與邊界

- `python3 scripts/check_branch_boundaries.py --branch codex/tier2-production-worker --base da6bb28fcd541d0d87e2b468f9a4157829f64419`：`branch_boundary=passed`
- `git diff --check`：passed
- 未呼叫真實 Bedrock、AWS CLI、SSM、S3 或 production release。
- `CO_STORY_PROCESS_TEST_DATABASE_URL` 專用 DSN 未提供時，真實 process/restart 相關測試維持明確 skip。

## Residual risk

- 現況不含 SQS、visibility heartbeat、DLQ 與分散式 worker deployment；僅驗證現有 CLI/Worker boundary。
- 真正 production worker restart 與 completion replay 的 durability 行為，仍仰賴後續整合批次進行環境化驗證。
