# Mock／HTTP 結局合約一致性 TDD 驗證

- Branch：`codex/mock-ending-parity`
- Baseline commit：`a15f137`
- Acceptance criterion：Mock adapter 必須與 HTTP adapter 回傳相同的目標點數、提前完成狀態及最大回合結局語意。

## Baseline

- Backend：`.venv/bin/python -m pytest backend/tests -q` → `28 passed`。
- Frontend：`node --test 'tests/**/*.test.js'` → `35 passed`。
- 工作樹乾淨；未執行 AWS 寫入。

## Red

- Commit：`a5104e7 test(red): specify mock ending parity`
- 僅變更：`web/tests/adapters/mock-game-api.test.js`。
- Targeted command：`node --test tests/adapters/mock-game-api.test.js`。
- 預期失敗原因：Mock adapter 尚未計算目標點數、尚未在非最終回合 100% 時進入 `COMPLETION_AVAILABLE`，且最終回合仍一律增加回合數。
- 實際結果：`9 passed / 3 failed`；`targetPoints` 實際為 0、最終狀態實際為 `COLLECTING_ACTIONS`。

## Green

- Commit：`897a8fb feat(green): align mock ending policy`
- 最小實作：集中更新目標點數與百分比，非最終回合依 100% 切換狀態，最大回合自動完成並產生結局；立即結局共用相同完成流程。
- Targeted test：`12 passed`。
- Regression suite：Backend `28 passed`；Frontend `38 passed`。

## Refactor

- 無額外 commit。Green 已將重複的百分比與完成流程分離為小型 helper；繼續抽象不會增加目前合約價值。
- 完整 regression suite 維持全綠。

## Sensitivity

- 暫時將最終回合判斷由 `round >= maxRounds` 改錯為 `round > maxRounds`。
- 「Mock adapter 最終回合自動完成並輸出部分成功與顯著代價」正確失敗，實際狀態由預期 `COMPLETED` 退化為 `COLLECTING_ACTIONS`。
- 變異已立即還原且未提交；還原後 Frontend `38 passed`、Backend `28 passed`。

## Browser／API／AWS 驗證

- 本切片未改 DOM、HTTP transport 或 FastAPI，公開行為由 adapter contract tests 驗證，因此不重複啟動 Browser／API 人工驗證。
- 三個獨立 Browser session 的多人 E2E 保留為下一個獨立驗證階段。
- AWS 寫入／新增資源／費用：無。
- 暫時伺服器：未啟動。
