# Tier 2 StoryJob publisher／reconciliation 驗證

- 日期：2026-08-29
- 風險：R3（PostgreSQL migration、跨 DB／SQS 一致性與 failure recovery）
- 範圍：repo-local strict TDD；未執行 AWS、未讀 S3、未呼叫 Bedrock、未傳送 SQS message
- Production 邊界：Web 維持 `sync`；本批未套用 `005` migration、未部署 publisher、未啟用 async

## Contract

- Producer 在既有 Room CAS／`story_jobs` transaction 內一併寫入 `story_job_dispatch_outbox`，message 只含 `schema_version=1` 與 opaque `job_id`。
- Publisher 以短效 lease、fencing token 與 `FOR UPDATE SKIP LOCKED` claim；同時多個 publisher 不得取得同一筆有效 lease。
- SQS SendMessage 失敗時不標記 dispatched，只保存固定錯誤碼並回到 pending。
- SendMessage 成功但 DB mark 失敗時保留 publishing lease；lease 到期後可 reconciliation，接受 SQS at-least-once duplicate，由既有 DB claim/fencing 去重。
- `005_create_story_job_dispatch_outbox.sql`為 append-only migration，並只回填既有 pending StoryJob。

## TDD 與驗證

- Red checkpoint：`6613d12`，新測試因缺少 `005`、dispatch adapter、publisher、SQS publish 與 producer outbox insert 而失敗。
- Green checkpoint：`1c3a44c`，targeted suite 全綠。
- R3 sensitivity：transaction 在 dispatch insert 後 fault 必須 rollback；stale lease 不得 mark；SQS 成功但 DB mark 失敗不得錯誤 release；非法 job ID 在 network call 前 fail closed。
- 完整 Backend regression：`752 tests collected`，exit code `0`；僅有既有 Starlette／httpx deprecation warning。
- `git diff --check`：通過。
- Branch boundary：此分支未登錄於 parallel branch policy，以 `--allow-unregistered` 檢查結果為 `branch_boundary=skipped:unregistered`；未修改治理 policy。

## Stop conditions

以下任一項成立即不得套用 migration、部署或啟用 async：

- Change Set 或 release 超出 `005` schema／publisher 所需範圍。
- Web producer role 不再是只允許指定 Story Queue 的 Get attributes／URL／Send。
- message 出現 Room snapshot、session、CSRF、cookie、transfer code、secret 或其他擴張欄位。
- 無法證明 DB commit 後 SendMessage failure 可保留 pending／到期 reconciliation。
- 成本上限 USD 35 或 2026-09-08 清理日改變。
