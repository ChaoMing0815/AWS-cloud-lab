# Support Agent PostgreSQL durability 驗證摘要

- Scope／risk／upstream source：R3 data-concurrency verification；ADR-0005、`docs/features/support-agent-persistence.md` 與 `codex/support-agent-durability` boundary。
- 測試環境：一次性、無 volume、僅綁定 localhost 的官方 `postgres:16-alpine` 容器；PostgreSQL major `16`。測試 DSN 與 credential 僅在 process environment 存在，未記錄於本檔案。
- Baseline：既有真實 restart／replay contract `2 passed`。
- Red commits：無；verification-only patch。新增的精確並行測試直接通過，未修改 production repository。
- Targeted verification：repository／process durability `12 passed`；兩個獨立 connection 以雙 barrier 在真實 pre-INSERT 競態重疊。
- Affected verification：Support Agent、Support migration、repository 與 process suite `56 passed`。
- Full regression：Backend 全部 `72` 個 test files 以執行器時限分段完成且均通過（未設定 DSN 的既有 optional PostgreSQL cases 維持明確 skip）；Frontend `96 passed`。
- Negative／sensitivity：暫時移除 divergent idempotency conflict guard 後，對應並行測試偵測到兩個 writer 成功並失敗；mutation 已立即還原。
- Rollback／residual risk：容器每次測試皆由 trap 移除並確認無殘留；沒有 production 連線、schema activation、API／UI 接線或外部提交。真實 production durability 仍需後續獨立 change envelope。
