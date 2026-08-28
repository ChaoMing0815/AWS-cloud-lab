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

## Bootstrap compatibility corrective（2026-08-28）

- Scope／risk／upstream source：R3 repo-local corrective；Sol safety gate確認舊production stable driver僅理解`digest-release`，而`migration-bridge`必須由exact scanned target image中的新driver完成。
- Baseline：Tier 3 delivery `16 passed`、legacy bootstrap `56 passed`、GitHub workflow `4 passed`；系統Python缺少`PyYAML`時只出現collection environment error，改用repo `.venv`後baseline全綠。
- Corrective Red：`6fb9631`。rendered SSM Document harness以只接受`digest-release`的fake old driver證明舊routing錯誤，並定義temporary asset、image-ID、preflight／release ordering、TOCTOU與schema stable-driver contract。
- Corrective Green：`8e636fc`。migration bridge pull前改用stable `digest-release preflight-only`；exact target image asset container經image-ID、root-only temporary asset metadata與SHA-256 fences後，使用同一temporary target driver做bridge preflight與release。schema activation仍由upgraded stable driver執行。
- Additional contract evidence：`4a8689d`使替換案例只改content並保留metadata，精確覆蓋second-hash fence；`64a1436`覆蓋target activation失敗時不寫verified marker且恢復previous runtime。
- Targeted／affected verification：new Document harness `10 passed`；Tier 2／Tier 3 affected suites與YAML parse通過。
- Full regression：Backend `620 passed, 11 skipped`；Frontend `96 passed`。
- Sensitivity：old preflight改回`migration-bridge`、target release置於target preflight前、移除regular／symlink gate、移除mode gate、略過asset-container image-ID比較、略過second-hash比較、恢復bridge migration call、提前寫marker、schema activation改用temporary driver；每一項對應目標測試皆失敗後立即還原。
- Rollback／residual risk：temporary assets只防替換／TOCTOU，不能限制已被main-only exact digest／scan／approval授權而以root執行的target driver。pre-mutation failure不改active state或marker；mutation後依driver恢復previous runtime，restore failure保留root-only forensic state。未建立或執行Change Set，未操作AWS／SSM／workflow dispatch／production deploy；PR #25仍為`DO NOT MERGE`。
