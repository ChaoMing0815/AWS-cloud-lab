# Tier 2 migration bridge 驗證摘要

- Scope／risk／upstream source：R3 repo-local migration bridge；ADR-0006、2026-08-28 Sol 設計 gate。
- Baseline：相關 migration／release／API／Worker／container contract suite 全綠；僅既有 Starlette deprecation warning。
- Red commit：`bcc891b`（inventory、sync composition、Worker second guard、release mode與marker contract）。
- Green commit：`d9d8a57`。
- Targeted verification：migration readiness、production composition、Tier 2 Worker、Tier 3 release workflow／driver contract 全綠。
- Negative／boundary：empty／gap／unknown／duplicate／malformed inventory、sync Worker、bridge marker missing／stale digest與unknown mode均 fail closed。
- Sensitivity：本機暫時破壞 migration call、inventory allowlist、sync flag、marker digest、rollback restore target與workflow bridge case；每次目標測試皆失敗後立即還原。
- Rollback／residual risk：schema activation只回復 verified bridge digest，不做 downgrade；未執行AWS、SSM、workflow dispatch或production deploy。真實 PostgreSQL process/restart gate仍需獨立非production DSN。

## Corrective review（2026-08-28）

- Corrective Red：`e305057`，證明 production mode default／normalization、applied inventory set／未排序查詢與固定 digest release output 都不符合 fail-closed contract。
- Corrective Green：`56b72e7`、`ce53674`。production database composition只接受 literal `sync`／`async`，Worker只接受 literal `async`；注入依賴的既有 security composition 不建立 producer／store，維持既有測試邊界。
- Migration runner：以 `ORDER BY version` 取得 tuple；新資料庫只允許由 audited `001` 起始，非空 applied inventory在任何 migration SQL／version INSERT 前經同一 validator 驗證。
- Release evidence：preflight與verified output均輸出實際 `release_mode`，不含 secret、ARN、instance ID或環境內容。
- Sensitivity：恢復 production default `async`、略過 applied inventory validator、重寫 output 為 `mode=digest-release`，三個目標測試皆失敗後立即還原。
- Final validation：targeted Tier 2／Tier 3 contract、Backend full regression、Frontend `96 passed`、YAML parse、`git diff --check`與branch boundary均通過；PostgreSQL process/restart需專用非production DSN的既有 cases維持 skip。
