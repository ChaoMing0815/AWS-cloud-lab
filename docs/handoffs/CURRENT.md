# CURRENT：目前工作交接

- 更新日期：2026-08-10
- Branch：`codex/llm-recovery-and-process-restart`
- 功能基準：`3dfff89`（LLM recovery、房主 UI 與 Uvicorn OS process restart 已完成）
- AWS：未操作；本機 Uvicorn 已停止，臨時 PostgreSQL 容器已停止並移除
- Regression：Backend `66 passed`、Frontend `60 passed`

## 已完成

- Retryable storyteller failure 自動重試一次；內容拒絕不重試。
- 失敗時保存 `RESOLUTION_FAILED`，不提交 canonical rules state。
- 房主可手動 retry 或使用 deterministic fallback；一般玩家看不到 recovery controls。
- 真正終止並重啟 Uvicorn OS process 後，完整 aggregate 與原 session cookies 可還原。
- Retry attempt mutation sensitivity 已通過。

## 下一個精確起點

依本機 MVP Test Plan，下一個基礎切片處理 polling 離線／reconnect UX：

```text
暫時性網路／5xx → 3／5／10 秒 bounded backoff
→ 保留最後 canonical 畫面 → 恢復後回到 3 秒 polling
→ 401／403 停止 retry；409 重新載入 canonical state
```

三玩家 Browser E2E、LLM recovery 與 Uvicorn OS process restart 已通過；完整本機 MVP 仍不得標示 release-ready，直到真實模型 schema／Guardrail、離線 UX、session lifecycle 與其餘 Test Plan 缺口完成。

## 固定邊界

- 嚴格 Red／Green／Refactor TDD。
- 基礎功能優先，不先做外觀優化或大型重構。
- 不重問已核准 Grill 與遊戲規則。
- 不執行 AWS 寫入；AWS 工作仍受成本與安全關卡約束。

本階段證據見 [`../evidence/2026-08-10-llm-recovery/tdd-validation.md`](../evidence/2026-08-10-llm-recovery/tdd-validation.md)；PostgreSQL 設計證據見 [`../evidence/2026-08-10-postgres-persistence/tdd-validation.md`](../evidence/2026-08-10-postgres-persistence/tdd-validation.md)。
