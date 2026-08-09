# Session Continue 與正式路由 TDD 驗證

- Branch：`codex/formal-entry`
- AWS：未登入、未呼叫、未建立資源。

## Baseline

- Backend：`39 passed`。
- Frontend：`51 passed`。
- Git 工作樹乾淨。

## Red／Green

- Backend Red `e8fd564`：`/api/v1/session/current` 四項測試均因 endpoint 不存在得到 `404`。
- Backend Green `aaf3bbc`：匿名、安全摘要、失效 session 與 canonical route mapping 完成。
- Frontend Red `62595d1`：adapter、Landing 與 markup 共五項因行為缺失失敗。
- Frontend Green `cc91632`：首頁 session restore、繼續入口與失效通知完成。
- Routes Red：`113718a`、`6b1aae3`。
- Routes Green：`4ae41d6`，完成 Play／Ending app shell 與 HTML 404。

## Sensitivity

- 將 `COMPLETED` 錯導至 `/play` 時，route mapping 測試正確失敗。
- 停用有效 session 顯示時，Landing 目標測試正確失敗。
- 恢復後 Backend `45 passed`、Frontend `56 passed`。

## Browser 驗證

- 舊 cookie 指向已不存在的 memory room 時，首頁顯示「目前的遊戲工作階段已失效」。
- 建立房間 `4QUBG3` 後返回首頁，顯示「房間 4QUBG3 · DRAFT」。
- 點擊「繼續遊戲」導向 `/host/setup`。
- `/room/4QUBG3/play` 與 `/room/4QUBG3/ending` 均載入 Game shell。
- 未知路由顯示「找不到此頁面」與首頁連結。
- `/demo` 顯示 `BONUS7` 與「教學 Demo · 不保存進度」，Console `0 errors`。
- 驗證頁籤與本機 FastAPI 均已停止。
