# 正式 Web App 入口 TDD 驗證

- Branch：`codex/formal-entry`
- Baseline commit：`5b5a466`
- Acceptance criterion：無有效 session 開啟 `/` 時，只顯示正式建立、加入與次要 Demo 入口，不載入 Demo 房間。

## Baseline

- Backend：`cd backend && ../.venv/bin/python -m pytest`
- 結果：`28 passed`；另有既存 Starlette／httpx deprecation warning。
- Frontend：`cd web && <workspace-node>/node --test 'tests/**/*.test.js'`
- 結果：`42 passed`。
- 環境註記：目前 shell 沒有 `npm`，首次 `npm test` 因 `command not found` 未進入測試，未計為 Red；改用專案 `package.json` 相同的 Node test command 後 baseline 全綠。
- AWS：未登入、未呼叫、未建立資源，費用影響為零。

## Red

- Commit：待建立。
- 僅變更的測試：待建立。
- 指令：待補。
- 預期失敗原因：目前根頁仍直接呈現 `BONUS7` Demo 遊戲介面，缺少正式 Landing 與獨立 `/demo` 入口。
- 實際失敗摘要：待補。

## Green

- Commit：待補。
- 最小實作：待補。
- Targeted test：待補。
- Regression suite：待補。

## Refactor

- Commit／無需重構理由：待補。
- Regression suite：待補。

## Browser／API／AWS 驗證

- 正面：待補。
- 負面：待補。
- 成本與清理：未執行 AWS 寫入；待完成功能後確認本機 server 已停止。
