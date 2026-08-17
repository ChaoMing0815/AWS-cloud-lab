# Migration 與 Readiness TDD 驗證紀錄

日期：2026-08-12  
範圍：版本化 PostgreSQL migration、獨立 migration CLI、schema-aware readiness。

## Red

1. 指令：`../.venv/bin/pytest -q tests/test_migration_readiness.py`
2. 結果：10 failed、1 passed。
3. 失敗皆為預期 assertion：尚未依序套用未執行 migration、尚未拒絕重複或非三位數版本檔名、CLI 尚未存在，以及 repository 尚未提供 schema-aware `is_ready()`。
4. Red checkpoint：`18a7147 test(red): require fixed-width migration versions`。

## Green

1. migration runner 僅接受 `NNN_description.sql`，對每個未套用版本在 transaction 中執行並記錄。
2. `python -m app.commands.migrate` 在缺少 `DATABASE_URL` 時以 stderr 回報且不顯示 DSN；Web boot 不會自動套用 migration。
3. PostgreSQL readiness 同時要求 `SELECT 1` 與所有預期 schema version 已存在。
4. 目標測試：11 passed。
5. 全後端回歸：224 passed、8 skipped。

## Refactor／故障注入

1. 刻意把 migration regex 從 `\\d{3}` 改為 `\\d+`。
2. 指令：`../.venv/bin/pytest -q 'tests/test_migration_readiness.py::test_migration_runner_rejects_duplicate_versions_and_invalid_filenames[filenames2]'`。
3. 結果：預期 failed，因 `1_ambiguous_version.sql` 不再被拒絕。
4. 已立即還原 regex 為固定三位數，並重跑目標測試：11 passed。

本切片未呼叫 AWS，也未連線至任何真實資料庫。
