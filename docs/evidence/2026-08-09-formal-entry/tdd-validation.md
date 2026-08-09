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

- `4753dd2 test(red): specify formal landing entry`：新增 `web/tests/ui/landing-markup.test.js`；因缺少 `#landingPage` assertion failure，確認不是 import／fixture／環境錯誤。
- `ce05de1 test(red): require app shell for demo route`：`GET /demo` 實際為 `404`，期待 `200`。
- `817c23b test(red): keep landing hidden in demo`：Browser 發現 Landing 與 Demo 同時可見後，新增 hidden visibility CSS contract；既有 CSS 缺少規則而 assertion failure。
- Targeted commands：
  - `<workspace-node>/node --test tests/ui/landing-markup.test.js`
  - `../.venv/bin/python -m pytest tests/test_health_and_static.py::test_fastapi_serves_app_shell_for_demo_route -q`

## Green

- `e4486fc feat(green): show formal landing at root`：新增可見 Landing 與建立／加入表單；root 不組裝 `MockGameApi`、不 mount `GamePage`，Demo game shell 預設 hidden。
- `2b41b0a feat(green): serve demo app shell`：FastAPI 只為 `/demo` 回傳既有 `index.html` app shell。
- `8c5ed1d fix(green): hide landing in demo mode`：新增 `.landing-shell[hidden] { display: none; }`。
- Targeted tests：Landing `2 passed`；Demo route `1 passed`。
- Regression suite：Backend `29 passed`；Frontend `44 passed`。

## Refactor

- 無獨立 refactor commit：本切片只加入一個靜態 Landing、路徑判斷與單一路由，尚未串接建立／加入 use case；提前抽象 router 會超出已測行為。
- Regression suite：Backend `29 passed`；Frontend `44 passed`。

## Browser／API／AWS 驗證

- 正面：`/` 的 Landing 可見、Game shell 不可見；建立／加入欄位與次要 Demo link 可由 DOM 讀取；root server log 無 `/rooms/current`。
- Demo：點擊次要入口後 `/demo` 回傳 `200`；Landing 不可見、Game shell 可見，頁首與 footer 都標示不保存進度。
- Browser Console：`0 errors`。
- 負面／發現：首次 `/demo` 為 `404`，由第二組 TDD 修正；首次 Demo 顯示時 Landing 未隱藏，由第三組 TDD 修正。
- 成本與清理：未執行 AWS 寫入；本機 FastAPI server 已停止，費用影響為零。

## 尚未完成

- session continue 與完整 router 將使用新的 Red cycle 實作。

## WP-1B 房主建房（2026-08-09）

- Red commits：`4b155f5`、`e2ef9ef`、`e84e8b4`、`c440dd1`。
- Green commits：`591bdb4`、`611f0b8`、`095907c`、`44c172b`。
- 完成 Room／Host session／第一位 Player／Player session 的單一冪等 operation；房主計入 3–5 人。
- 拒絕空白暱稱、暱稱變更重用同一 idempotency key，並拒絕 client-supplied `player_id`。
- Landing 建房成功導向 `/host/setup`；Browser 驗證顯示 `1 / 5`、房主暱稱與世界表單。
- Browser 發現 deep-route 重新整理的相對資產路徑錯誤，已以 Red／Green 改為同源絕對路徑。
- Sensitivity：暫時移除房主 Player 建立時，目標測試正確失敗；恢復後通過。
- Regression：Backend `34 passed`；Frontend `46 passed`；Browser Console `0 errors`。
- AWS：未登入、未呼叫、未建立資源，費用影響為零。

## WP-1C 房號加入（2026-08-09）

- Red commits：`d0b4b34`（後端）、`89fb76c`（前端）。
- Green commits：`755dd0d`（後端）、`d48212e`（前端與 Lobby deep link）。
- `POST /api/v1/rooms:join` 不依賴 current room；同一 operation 完成 room-code lookup、狀態／容量／暱稱檢查、Player 建立與 opaque Player session cookie。
- 拒絕 `ROOM_CODE_INVALID`、`ROOM_NOT_FOUND`、`ROOM_NOT_JOINABLE`、`ROOM_FULL`、`NICKNAME_DUPLICATE`、client-supplied `player_id` 與 `IDEMPOTENCY_KEY_REUSED`；replay 不重複建立玩家。
- Sensitivity：暫時移除 `LOBBY` gate 後，草稿房間測試由預期 `409` 變成 `201` 並正確失敗；恢復後全綠。
- Regression：Backend `39 passed`；Frontend `51 passed`。
- Browser：建立並確認房間 `772JV8`，以小寫 `772jv8`＋暱稱加入後導向 `/room/772JV8/lobby`，玩家數為 `2 / 5`；重新整理維持 Lobby，Console `0 errors`。
- 清理：本機 FastAPI 已停止；未登入或操作 AWS，費用影響為零。
