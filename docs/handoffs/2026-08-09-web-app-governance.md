# 下一對話任務交接：正式 Web App 入口

- 交接日期：2026-08-09
- 目前分支：`main`（WP-0 文件變更尚未 commit）
- AWS 寫入／新增資源／費用：無
- Production code 變更：無
- 本機伺服器：未啟動

## 本輪完成

- 確認本輪 Grill 以既有 MVP Spec 為基礎，沒有重問骰子、星火、角色屬性、回合與結局規則。
- 建立[文件權威索引](../product/source-of-truth.md)，避免 checklist、架構目標與程式現況互相覆蓋。
- 建立[Web App User Flow](../product/user-flow.md)與[Screen States](../product/screen-states.md)。
- 建立小型專案使用的[Feature Spec 規則](../features/README.md)與[本機 MVP Test Plan](../qa/local-mvp-test-plan.md)。
- 入口切片已整理成[正式入口與房間加入 Feature Spec](../features/entry-and-room-join.md)，狀態為 `Approved for TDD`。
- 本輪六項補充決策已保存於[核准紀錄](../governance/approval-log.md)。
- README、task list、checkpoints、session 設計與 deployment log 已同步。

## 已核准且不可重問的內容

- 房主也是玩家；建房時同時取得 Host／Player 身份並計入 3–5 人。
- `/demo` 是次要教學入口，使用隔離 Mock，不呼叫正式 API／LLM／DB，不保存進度。
- 跨裝置取回由房主核准，使用 10 分鐘一次性轉移碼，成功後撤銷舊 session。
- 進行中房間最後活動後 7 天到期；結局後保留 7 天；房主可提前永久刪除。
- 世界生成與回合 retry／fallback 沿用正式 Spec 及 approval log，不再重新 grill。

## 下一步：WP-1 第一個嚴格 TDD 切片

依[入口 Feature Spec](../features/entry-and-room-join.md)執行：

1. 確認工作樹與完整測試 baseline。
2. 建立 `codex/formal-entry` 分支。
3. Red：無 session 開啟 `/` 時顯示 Landing，且不載入 Demo room。
4. Green：最小 LandingPage／router wiring；尚不提前實作 room-code API。
5. Refactor、完整 regression、Browser 驗證與 evidence。
6. 完成後再以新的 Red 進入「房主建房同時成為玩家」。

## 邊界

- 所有程式行為依 `docs/testing-strategy.md` 保存 Red／Green／Refactor 證據。
- 不以修改既有測試期待來配合實作。
- 不變更遊戲規則與 canonical state。
- 不執行 AWS 寫入，不呼叫真實 Bedrock。
