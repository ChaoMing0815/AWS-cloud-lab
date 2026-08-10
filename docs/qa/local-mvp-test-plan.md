# 本機 Web MVP Test Plan

- 狀態：Active target
- Owner：QA
- Source of Truth：是，僅負責本機 Web MVP release gate
- Depends on：[MVP Spec](../specs/text-rpg-mvp-spec.md)、[Screen States](../product/screen-states.md)、[測試策略](../testing-strategy.md)
- 最後檢視：2026-08-09

> 嚴格 Red／Green／Refactor 步驟與 evidence 格式不在此重複，全部引用測試策略。本文件定義「哪些使用者旅程必須通過」。

## Release Gate

本機 MVP 只有同時符合下列條件才可標示完成：

1. Backend、frontend、repository contract 與 E2E suite 全綠。
2. 三個獨立 browser contexts 可完成正式一回合，不能使用 `/demo` 代替。
3. Process restart 後 room、players、characters、round、results 與 story 仍存在。
4. LLM timeout／schema／內容拒絕可進入 retry 或 deterministic fallback，canonical state 不被改寫。
5. 未授權、CSRF、version conflict、replay、房間滿員與 session 失效均有負面測試。
6. Loading、empty、error、offline、reconnected 與 completed 狀態可由 Browser 驗證。
7. Console 無未處理錯誤；畫面不洩漏 token、cookie、stack、SQL 或 AWS credential。

## 測試層級

| 層級 | 主要責任 |
| --- | --- |
| Domain unit | 規則、狀態轉移、期限、結果分類 |
| Application unit | Use case orchestration、錯誤分類、retry／fallback |
| Repository contract | Memory 與 PostgreSQL 對相同 contract 的一致性 |
| API integration | Session、CSRF、idempotency、version、serialization、transaction |
| UI | 各 page 的 idle、loading、error、offline、permission 與 success |
| Browser E2E | 真正首頁、三個 session、完整一回合、重整與結局 |

## P0 使用者旅程

1. 房主在首頁建立房間並同時成為第一位玩家。
2. 兩位玩家以 room code 加入，三人各自完成角色。
3. 房主開始，三個 context 各自提交隱藏 action。
4. 房主擲骰，三位玩家完成星火決策，房主結算。
5. 故事顯示且回合只推進一次；refresh 後狀態一致。
6. 進度達成或最大回合後產生正確結局。

## 必要負面案例

- 無效／不存在 room code、重複暱稱、第六位玩家、開始後加入。
- 非房主執行 Host mutation、玩家存取他人未揭露 action。
- 錯誤／缺少 CSRF、過期 session、舊 room version、重複 idempotency key。
- Polling 離線、暫時性 `5xx`、恢復連線與取消。
- LLM timeout、throttling、schema invalid、內容拒絕與 fallback。
- 角色轉移碼錯誤、過期、replay；成功轉移後舊 session 失效。
- 房主刪除後所有資料不可讀；到期清理不影響未到期房間。

## 非功能檢查

- Desktop 主 Demo 流程可用；窄螢幕可閱讀。
- 鍵盤可完成建立、加入、角色、action 與主要確認流程。
- 錯誤不只以顏色表達；label 與 focus 行為可用。
- 同一 mutation 不因 double-click 或 retry 產生重複副作用。
- 本機 Demo 不呼叫 AWS 或產生雲端費用。

## 已知目前缺口

- 正式 Landing、room-code join、session continue 與基本 deep routes 已完成。
- 三個獨立 browser contexts 已完成正式單回合 E2E；結局 Browser E2E 仍待 release gate 一併確認。
- Polling 離線狀態、session lifecycle、PostgreSQL 與 LLM recovery 尚未完成。

因此目前不得將本機 Web MVP 標示為 release-ready。
