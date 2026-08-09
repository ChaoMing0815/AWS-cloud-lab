# CURRENT：目前工作交接

- 更新日期：2026-08-10
- Branch：`codex/formal-entry`
- 功能基準：`a9ca393`（三玩家 E2E 發現的 canonical route 缺陷已完成 Green）
- AWS：未操作；本機伺服器已停止
- Regression：Backend `45 passed`、Frontend `58 passed`

## 已完成

- 8/10 原定基礎任務完成：Session Continue、安全摘要、正式 deep routes、HTML 404、Demo 隔離。
- 三個隔離 `*.localhost` origin 已完成正式一回合：角色、開始、三人行動、擲骰、星火、結算與三端 refresh。
- 三端一致顯示 Round `02`、正式進度／危機 `3（10%）`、各自角色 Session 隔離且 Console `0 error`。
- Browser E2E 發現並以嚴格 TDD 修正 setup／lobby 未同步至 canonical `/play` 的缺陷。

## 下一個精確起點

建立 PostgreSQL repository contract，先以測試定義 Memory 與 PostgreSQL adapter 必須共享的行為：

```text
repository contract → schema / migration → PostgreSQL adapter
→ process restart → room / players / characters / round / results / story 仍存在
```

三玩家 Browser E2E 已通過；完整本機 MVP 仍不得標示 release-ready，直到 restart persistence 與其餘 Test Plan 缺口完成。

## 固定邊界

- 嚴格 Red／Green／Refactor TDD。
- 基礎功能優先，不先做外觀優化或大型重構。
- 不重問已核准 Grill 與遊戲規則。
- 不執行 AWS 寫入；AWS 工作仍受成本與安全關卡約束。

詳細入口歷史見 [`2026-08-09-web-app-governance.md`](2026-08-09-web-app-governance.md)；8/10 證據見 [`../evidence/2026-08-10-session-continue/tdd-validation.md`](../evidence/2026-08-10-session-continue/tdd-validation.md)與[`../evidence/2026-08-10-three-player-browser-e2e/validation.md`](../evidence/2026-08-10-three-player-browser-e2e/validation.md)。
