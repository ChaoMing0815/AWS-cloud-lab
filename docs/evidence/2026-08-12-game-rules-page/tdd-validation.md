# 輕量遊戲規則頁驗證摘要

- 範圍／風險：R2；既有 MVP 規則的唯讀玩家說明頁。
- Red：`a634e15 test(red): specify lightweight game rules page`；`/rules` 回傳 404，符合尚未提供獨立規則頁的預期失敗。
- Green：`a838dd0 feat(green): add lightweight game rules page`；首頁導覽與 `/rules` 提供開局、回合、骰子、星火、結局及職責摘要，無 API mutation／session side effect。
- Targeted：`tests/test_health_and_static.py`，8 passed。
- Browser：本機 `http://127.0.0.1:8000/rules` 已驗證入口、返回首頁與規則內容皆可見。
- Full regression：Backend `238 passed, 8 skipped`。
- Residual risk：目前 shell 缺 Node／npm，web Node suite 未能重跑；規則頁已由 Browser 實測，Node suite 留待 production-parity gate 的前端環境修復後執行。
