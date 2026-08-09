# 房間狀態 Polling TDD 驗證

- Branch：`codex/room-polling`
- Baseline commit：`c2d332f`
- Acceptance criterion：頁面以串行 polling 同步 canonical room state，不得重疊 request；結局完成或呼叫停止時不得繼續排程。

## Baseline

- Backend：`28 passed`。
- Frontend：`38 passed`。
- 工作樹乾淨；未執行 AWS 寫入。

## Red

- Commit：`330cbfc test(red): specify room polling lifecycle`
- 僅新增：`web/tests/ui/game-page-polling.test.js`。
- Targeted command：`node --test tests/ui/game-page-polling.test.js`。
- 預期失敗原因：`GamePage` 尚無 `startPolling`、`pollOnce` 與 `stopPolling`。
- 實際結果：`0 passed / 4 failed`，失敗皆為目標 lifecycle 尚不存在。

## Green

- Commit：`f3aaecb feat(green): poll room state without overlap`
- 最小實作：以 3 秒 `setTimeout` 串行同步；每次 request 完成後才排定下一次；busy／in-flight／completed 狀態不發出新 request；`stopPolling` 取消已排定 timer。
- Targeted test：`4 passed`。
- Regression suite：Backend `28 passed`；Frontend `42 passed`。

## Refactor

- 無額外 commit。Polling lifecycle 已拆成 `startPolling`、`schedulePolling`、`pollOnce`、`stopPolling`，目前沒有需要再抽象的重複行為。

## Sensitivity

- 暫時移除 `pollInFlight` 防護。
- 「GamePage 不允許重疊的 polling request」正確失敗，load 次數由預期 1 變為 2。
- 變異已還原且未提交；還原後完整 suite 全綠。

## Browser／API／AWS 驗證

- 以 `127.0.0.1:8765` 啟動 FastAPI 同源頁面。
- 頁面顯示「本機 FastAPI 模式」、房間 `BONUS7`，無水平溢出。
- 初次載入後，server access log 持續出現 `/api/v1/rooms/current` 200，證明 3 秒 polling 實際運作。
- Browser Console：`0 errors`；頁面沒有顯示錯誤 feedback。
- 驗證完成後已關閉分頁並停止 8765 伺服器。
- AWS 寫入／新增資源／費用：無。

## 獨立瀏覽器限制

目前可控制的瀏覽器分頁共享同一 cookie 空間；開三個分頁不能代表三個獨立玩家 session，因此未將共享 cookie 的結果冒充三瀏覽器 E2E。真正的三玩家 Browser E2E 仍需不同 browser／profile 完成。
