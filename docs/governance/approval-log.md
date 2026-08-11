# 產品與實作核准紀錄

- 狀態：Active
- Owner：專題使用者
- Source of Truth：是，僅記錄已核准補充決策
- 最後檢視：2026-08-11

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

## 2026-08-11 Session lifecycle observable contract

| 決策 | 類型 | 核准內容 | 影響 |
| --- | --- | --- | --- |
| 活動與期限 | 補充 | 成功的加入、玩家行動、星火、回合結算與房主 mutation 延長對應 room／actor session；GET、polling、拒絕及失敗操作不延長。 | Expiry、activity refresh、負面測試 |
| 過期錯誤 | 補充 | 過期 read 回 `SESSION_NOT_FOUND`；mutation 回對應 session-required 錯誤，且不先洩漏 CSRF／version 細節。 | API、authorization、UX |
| 新舊轉移碼 | 補充 | 同一 Player 發行新 transfer code 時，舊未使用 code 立即失效。 | Repository、replay、concurrency |
| 房間狀態 | 補充 | DRAFT／LOBBY／進行中／已滿房可轉移既有 Player；完成後 7 天保留期內允許唯讀轉移；過期房禁止發碼與兌換。 | Transfer eligibility、ending UX |
| 房主的 Player | 補充 | 房主轉移自己的 Player 時只撤銷 Player session；原裝置 Host session 保留，UI 必須提示 Host 權限未移轉。 | Session rotation、UI、安全提示 |

核准方式：使用者先核准前三項，再於說明取捨後核准後兩項；五項均已完成核准。
