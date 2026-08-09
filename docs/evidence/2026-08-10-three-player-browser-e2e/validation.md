# 三玩家完整回合與 canonical route 驗證

- 日期：2026-08-10
- Branch：`codex/formal-entry`
- Baseline commit：`b18a837`
- AWS：未操作；只使用本機 FastAPI memory repository

## Baseline

- Backend：`.venv/bin/python -m pytest -q` → `45 passed`
- Frontend：bundled Node 執行 `node --test 'tests/**/*.test.js'` → `56 passed`
- 工作樹：乾淨

## Browser E2E

以三個獨立且安全的 `*.localhost` origin 建立 Host／Player session，完成：

```text
create → world → join ×2 → character ×3 → start
→ action ×3 → roll → spark ×3 → resolve → refresh ×3
```

驗證結果：

- Lobby 顯示 `3 / 5`，三人各自完成三點配點。
- 各 origin 只顯示自己的角色身分，未互相覆寫 Session。
- 三個隱藏行動收齊後才允許房主擲骰。
- 三位玩家完成星火決策後，房主成功結算一次。
- 三端重新整理後一致顯示 Round `02`、正式進度 `3（10%）`、正式危機 `3（10%）`、本回合行動 `0`。
- 三端 Console 均為 `0 error`。
- 未呼叫 Bedrock、AWS API 或其他計費服務。
- 驗證完成後已關閉 Browser 測試分頁並停止 `127.0.0.1:8000` 本機伺服器。

## E2E 發現與嚴格 TDD 修正

第一輪 Browser 驗證發現：canonical state 已進入遊戲，但網址仍停在 `/host/setup` 或 `/lobby`，不符合核准 User Flow。

### Red

- `8fdfcf7 test(red): require canonical game route sync`
- `d0c36af test(red): cover canonical room route states`
- Targeted test：`1 passed, 2 failed`
- 預期失敗：`COLLECTING_ACTIONS` 未導向 `/room/ABCD23/play`，setup／lobby／ending 也未同步。

### Green

- `a9ca393 fix(green): sync canonical game routes`
- `GamePage` 在 operation 與 polling 取得 canonical room 後同步 route。
- 正式模式使用 `history.replaceState`；隔離的 `/demo` 不改路由。
- Targeted test：`3 passed`
- Regression：Backend `45 passed`、Frontend `58 passed`

### Refactor

- 無需額外重構；最小實作維持既有 `GamePage` 與 composition 邊界。

### Sensitivity

- 暫時把遊戲中 route 從 `/play` 改成 `/lobby`。
- Targeted test 正確失敗：實際 `/room/ABCD23/lobby`，預期 `/room/ABCD23/play`。
- 還原後 Backend `45 passed`、Frontend `58 passed`。

### 修正後 Browser 驗證

- Host、Player 2、Player 3 在開始遊戲後均切換至各自 origin 的 `/room/NAYTLJ/play`。
- 結算並重新整理後三端仍位於 `/play`，canonical state 與角色身分一致，Console `0 error`。

## 尚未完成

- memory repository 在 process restart 後不保存資料。
- 下一個 release-gate 切片為 PostgreSQL repository contract、schema／migration 與 restart persistence。
