# Feature Specs

- 狀態：Active
- Owner：Product／Engineer／QA
- Source of Truth：各功能只對自己的差異與 acceptance criteria 負責
- 最後檢視：2026-08-11

小型專案不為每項功能重寫 PRD、SRS、TRD 與 Test Plan。Feature Spec 只補充上游 Approved Spec／ADR／approval log 尚未定義的產品差異；若沒有產品差異，可直接依上游來源進入風險式 TDD。

## 每份 Feature Spec 最低內容

1. 上游核准來源與真正新增的差異；沒有差異時明記「無產品差異」。
2. 使用者可觀察的 acceptance criteria、必要 contract 與 non-goals。
3. 風險等級 R1–R3，以及只有該 feature 特有的驗證／rollback 邊界。

上游已核准的行為可標示 `Ready for TDD`，不需再次取得整份 Feature Spec 核准。R1 以 commits／測試摘要為證據；R2／R3 每個 cohesive feature 最多一份短 validation manifest。

## 目前切片

| Feature | 狀態 | 下一關 |
| --- | --- | --- |
| [正式入口與房間加入](entry-and-room-join.md) | Implemented baseline | Accessibility／Browser release gates |
| [Polling 離線與重新連線 UX](polling-offline-reconnect.md) | Implemented＋Browser verified | AWS HTTPS release gate |
| [Session lifecycle／角色轉移](session-lifecycle-and-transfer.md) | Implemented（R3） | Durable idempotency 留待 multi-process batch |
| PostgreSQL persistence | Implemented baseline | Multi-process CAS／durable idempotency 另立 R3 batch |
| LLM round recovery | Implemented baseline | 真實 Bedrock schema／Guardrail 另立 R2／R3 batch |
