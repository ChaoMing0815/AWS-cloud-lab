# Polling 離線與重新連線 UX

- 狀態：Approved for TDD
- Owner：Product／Engineer／QA
- 核准來源：2026-08-10 使用者明確要求接續此基礎切片
- Depends on：[Screen States](../product/screen-states.md)、[本機 MVP Test Plan](../qa/local-mvp-test-plan.md)、[測試策略](../testing-strategy.md)
- 最後檢視：2026-08-10

## 目標

多人同步頁在短暫斷線或 API 暫時失敗時保留最後一次確認的 canonical state，清楚說明重試狀態，並在連線恢復、session 失效或版本衝突時採取可預期行為。

## Acceptance criteria

1. 正常 polling 間隔為 3 秒，同一時間最多一個 request。
2. 網路錯誤或 `5xx` 不清空、不覆寫最後一次成功載入的 room 畫面；畫面以文字顯示離線與下次重試時間。
3. 連續暫時失敗使用 `3s → 5s → 10s → 10s` bounded backoff；不得無限制增加等待時間。
4. 暫時失敗後第一次成功載入 canonical state 時，畫面顯示已重新連線，後續 polling 恢復 3 秒。
5. `401/403` 停止 polling，不再排程 retry，並顯示 session 已失效與回首頁的下一步。
6. `409` 不以舊 state 覆寫；立即再載入一次 canonical state。成功時更新畫面並回到 3 秒 polling。
7. 結局完成、離開同步頁或主動停止時，維持既有取消 polling 行為。

## UI 與 contract 差異

- 遊戲頁新增獨立的連線狀態區，使用 `role="status"` 與 polite live region；不得覆蓋 mutation feedback。
- `GamePage` 只根據 error 的 HTTP `status` 分類 polling recovery；不更動 API、domain rule 或 canonical room schema。
- 暫時失敗期間 `GamePage.room` 與已 render 的 DOM 保持最後一次成功值。

## 案例

| 類型 | 輸入 | 可觀察結果 |
| --- | --- | --- |
| 正常 | poll 成功 | 更新 canonical state，3 秒後再 poll |
| 離線 | fetch 拋出無 status 的錯誤 | 保留畫面，顯示離線，依 bounded backoff 重試 |
| 暫時性服務錯誤 | `500–599` | 與離線相同，不顯示原始 stack |
| 恢復 | 暫時失敗後成功 | 更新畫面、顯示重新連線、backoff 重設為 3 秒 |
| Session 失效 | `401/403` | 停止 polling，顯示回首頁下一步 |
| Version conflict | `409` | 立即 reload canonical state；成功後回到 3 秒 |

## 不在本切片

- Session transfer／revoke／reassign 的完整流程。
- Service Worker、離線 mutation queue、WebSocket 或跨分頁同步。
- 自動重送 mutation；本切片只處理讀取 canonical state 的 polling。
- Browser E2E 的網路攔截自動化；先完成 deterministic UI tests，Browser 驗證另記錄限制。

## 修改邊界

- 允許：`GamePage` polling orchestration、遊戲頁連線狀態 markup／style、相關 frontend tests、TDD evidence 與 handoff。
- 不得：更動 backend API contract、遊戲規則、repository、LLM recovery 或 AWS 資源。

## TDD、驗證與 rollback

- Red：用 deterministic scheduler 與失敗序列先證明 backoff、preserve state、reconnect、session stop、`409` reload 尚未存在。
- Green：只加入錯誤分類、計數器、排程 delay 與連線狀態呈現。
- Refactor：僅在全綠後整理命名或重複分類；不新增行為。
- Sensitivity：暫時把 backoff 上限或 session stop 判斷改錯，確認目標測試失敗後還原。
- Regression：Frontend 全套與 Backend 全套；不執行 AWS 寫入。
- Rollback：還原本切片 commits，即恢復固定 3 秒 polling 與既有畫面。
