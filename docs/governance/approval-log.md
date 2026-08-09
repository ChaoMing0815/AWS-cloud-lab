# 產品與實作核准紀錄

- 狀態：Active
- Owner：專題使用者
- Source of Truth：是，僅記錄已核准補充決策
- 最後檢視：2026-08-09

## 使用原則

本紀錄不複製正式 MVP Spec。若決策只是確認既有規格，標示「既有規格確認」；只有新增細節才標示「補充」。後續變更必須新增紀錄，不得靜默改寫舊決策。

## 2026-08-09 Web App 流程 Grill

| 決策 | 類型 | 核准內容 | 影響 |
| --- | --- | --- | --- |
| 房主身分 | 補充 | 房主是建房發起人，也是 3–5 位玩家之一；建房時同時取得 Host／Player 身份。人工 GM／DM 不存在，故事主持交由 LLM。 | Create room、Lobby 人數、session、E2E |
| 教學 Demo | 補充 | 保留首頁次要入口；固定 Mock、虛擬玩家、不呼叫正式 API／LLM／DB、不建立正式 session、不保存進度。 | Router、Demo composition、產品標示 |
| 跨裝置重新指派 | 既有規格＋補充 | 仍由房主核准；使用 10 分鐘一次性轉移碼，成功後撤銷舊 session。 | Session、audit、負面測試 |
| 房間與 session 期限 | 既有規格＋補充 | 進行中房間最後活動後 7 天到期；完成房間自結局後保留 7 天；session 不晚於房間到期，房主可提前永久刪除。 | Persistence、cleanup、UX |
| 世界草稿生成 | 既有規格確認 | 可完全手動或由 3–5 關鍵字生成；每房最多首次生成＋重新生成一次；失敗保留輸入，可重試或改手動，確認前不得進 Lobby。 | LLM contract、成本 UI |
| 回合敘事失敗 | 既有規格確認＋補充 | 自動重試一次；仍失敗後房主可手動重試一次或使用 deterministic fallback。Fallback 不改 canonical state；記錄 model、latency、token、retry、fallback 與估計成本，不記錄憑證。 | Storyteller、observability、QA |

核准方式：使用者於對話中逐項確認；Grill 進度 `6／6` 完成。
