# CURRENT：目前工作交接

- 更新日期：2026-08-10
- Branch：`codex/postgres-persistence`
- 功能基準：`c97c7b9`（PostgreSQL application restart persistence 已完成 Green）
- AWS：未操作；本機伺服器未啟動，臨時 PostgreSQL 容器已停止並移除
- Regression：Backend `56 passed`、Frontend `58 passed`

## 已完成

- ADR-0003、PostgreSQL schema／migration runner、adapter 與 Memory／PostgreSQL 共用 contract 已完成。
- `DATABASE_URL` runtime composition 已完成；未設定時仍使用 Memory adapter。
- 兩個獨立 FastAPI application instance 已驗證 room、房間碼、Host／Player session 可跨重啟還原。
- Repository contract 已通過遺失 story `entries` 的 mutation sensitivity。

## 下一個精確起點

建立 LLM failure recovery contract，先以 application port 測試定義 timeout／throttling／schema invalid／內容拒絕：

```text
Storyteller failure taxonomy → bounded retry → deterministic fallback
→ canonical room/version 不被部分失敗改寫 → API/UI 可理解狀態
```

三玩家 Browser E2E 與 application restart persistence 已通過；完整本機 MVP 仍不得標示 release-ready，直到 LLM recovery、正式 process／container restart 與其餘 Test Plan 缺口完成。

## 固定邊界

- 嚴格 Red／Green／Refactor TDD。
- 基礎功能優先，不先做外觀優化或大型重構。
- 不重問已核准 Grill 與遊戲規則。
- 不執行 AWS 寫入；AWS 工作仍受成本與安全關卡約束。

詳細入口歷史見 [`2026-08-09-web-app-governance.md`](2026-08-09-web-app-governance.md)；本階段證據見 [`../evidence/2026-08-10-postgres-persistence/tdd-validation.md`](../evidence/2026-08-10-postgres-persistence/tdd-validation.md)。
