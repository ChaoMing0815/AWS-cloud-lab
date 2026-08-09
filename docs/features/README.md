# Feature Specs

- 狀態：Active
- Owner：Product／Engineer／QA
- Source of Truth：各功能只對自己的差異與 acceptance criteria 負責
- 最後檢視：2026-08-09

小型專案不為每項功能重寫 PRD、SRS、TRD 與 Test Plan。每個 production 行為切片以一份 Feature Spec 串起上游規格與嚴格 TDD。

## 每份 Feature Spec 最低內容

1. 狀態、Owner、相依規格與不在範圍。
2. 使用者可觀察的 acceptance criteria。
3. API／頁面 contract 的必要差異。
4. 正常、拒絕、錯誤與恢復案例。
5. 允許修改與不得碰觸的邊界。
6. Red／Green／Refactor、Browser／API 驗證與 rollback。

只有 `Approved for TDD` 的 Feature Spec 可以開始 production code。實作證據另存 `docs/evidence/<date>-<slice>/`，不塞回規格本文。

## 目前切片

| Feature | 狀態 | 下一關 |
| --- | --- | --- |
| [正式入口與房間加入](entry-and-room-join.md) | Approved for TDD | 建立 baseline 與第一個 Red commit |
| Polling 離線狀態 | Planned | 入口完成後整理 Feature Spec |
| Session lifecycle／角色轉移 | Planned | 入口與 Lobby 完成後整理 Feature Spec |
| PostgreSQL persistence | Planned | 建立資料層 ADR |
| LLM world／round recovery | Planned | PostgreSQL contract 穩定後整理 Feature Spec |
