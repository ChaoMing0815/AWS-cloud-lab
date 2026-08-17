# Polling 離線與重新連線 UX TDD 驗證

- Branch：`codex/polling-offline-reconnect`
- Baseline commit：`f6c184e`
- Acceptance criterion：網路／`5xx` 以 3、5、10 秒 bounded backoff 重試並保留 canonical 畫面；恢復後回到 3 秒；`401/403` 停止；`409` 立即 reload canonical state。

## Baseline

- Targeted：`node --test tests/ui/game-page-polling.test.js` → `4 passed`。
- Frontend：`node --test 'tests/**/*.test.js'` → `60 passed`。
- Backend：`.venv/bin/python -m pytest backend/tests` → `59 passed, 7 skipped`；skip 是未提供外部 PostgreSQL test URL 的既有條件。
- 環境更正：系統 shell 沒有 Node，改用 Codex workspace bundled Node；第一次誤用系統 Python 因缺少 `fastapi` 等 dependency 而 collection error，不算 baseline 或 Red，正式 Backend baseline 使用 repository 既有 `.venv`。

## Red

- Commit：`a34f59e`（`test(red): require polling offline recovery UX`）。
- 僅變更：`web/tests/ui/game-page-polling.test.js`。
- 指令：`node --test tests/ui/game-page-polling.test.js`。
- 結果：既有 `4 passed`，新增 `5 failed`。
- 預期失敗原因：既有 `pollOnce()` 讓暫時錯誤、`401/403` 與 `409` 直接 reject，且頁面沒有 `pollingStatus` live region。
- 實際失敗摘要：4 個 `assert.doesNotReject` 因未處理的 network／HTTP error 失敗；markup assertion 因缺少 `#pollingStatus` 失敗。沒有 syntax、import、fixture 或環境錯誤。

## Green

- Commit：`ce80b79`（`feat(green): recover polling after transient failures`）。
- 最小實作：只在 `GamePage` 加入 polling error 分類、bounded delay、canonical reload／preserve 與 live status；新增一個 status markup 及對應樣式。
- Targeted：`9 passed`。
- Frontend regression：`65 passed`。
- Backend regression：`59 passed, 7 skipped`。

## Refactor

- 無額外 refactor commit：Green 已把 polled room 套用、成功重設、backoff 推進與 status 呈現分成小方法；再抽象會超出此基礎切片。
- 還原 sensitivity mutation 後：Targeted `9 passed`、Frontend `65 passed`、Backend `59 passed, 7 skipped`。

## Sensitivity

- 暫時變異：把 backoff 上限由 `10000` 改為 `30000` 毫秒，未提交。
- 指令：`node --test --test-name-pattern='bounded backoff' tests/ui/game-page-polling.test.js`。
- 結果：`1 failed`；測試精確抓到實際 delay `[3000, 3000, 5000, 30000, 30000]` 不符合預期 `[3000, 3000, 5000, 10000, 10000]`。
- 還原：已用 patch 恢復 `10000`，工作樹回到 Green commit 且完整 suite 再次全綠。

## Browser／API／AWS 驗證

- 正面：deterministic UI test 驗證 reconnect 更新 canonical state、只 render 一次並恢復 3 秒。
- 負面：network、`5xx`、`401`、`403`、`409`、backoff 上限、保留最後 state 與停止 retry 均有 UI test。
- Accessibility：`#pollingStatus` 使用 `role="status"`、`aria-live="polite"` 與完整文字，不只依賴顏色。
- Browser：本基礎切片未執行真實 Browser 網路攔截；本機 MVP release gate 仍保留 Browser offline／reconnected 驗證缺口。
- API：未修改 backend contract。
- AWS：未呼叫 AWS API、未執行 AWS 寫入、未產生雲端費用。

## 已知限制與下一步

- 本切片不重送 mutation，不包含 session transfer／revoke／reassign。
- 下一個本機 MVP 基礎切片是 session lifecycle；Browser release gate 需再以實際 network interception 驗證離線與恢復畫面。
