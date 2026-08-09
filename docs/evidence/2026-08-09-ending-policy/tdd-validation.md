# 結局策略嚴格 TDD 驗證

- 日期：2026-08-09
- 分支：`codex/ending-policy`
- Baseline：`81f04f6`
- AWS 寫入／新增資源／費用：無

## 規格邊界

- 房主建立房間時選擇 `4／6／8` 回合。
- 目標點數為 `初始玩家數 × 2 ×（最大回合數 - 1）`；正式進度百分比上限為 100%。
- 最終回合依進度判定：`100%` 完整成功、`60–99%` 部分成功、`0–59%` 失敗。
- 危機代價：`0–39%` 低、`40–69%` 顯著、`70–100%` 重大；危機本身不提前結束遊戲。
- 最終回合自動完成。提前達到 100% 時進入 `COMPLETION_AVAILABLE`，只有房主可選擇立即結束或繼續探索。
- Storyteller 只產生敘事，不得修改點數、百分比、結局或代價。

## Red → Green → Refactor 證據

| 階段 | Commit | Red／Green 證據 |
| --- | --- | --- |
| 結局規則 Red | `68e897e` | 新測試因狀態仍回到 `COLLECTING_ACTIONS`、缺少百分比而失敗。 |
| 結局規則 Green | `cfb0916` | 套用最大回合、提前完成、百分比、結局與代價規則。 |
| 邊界加固 | `ee87c0b` | 增加 4／6／8 回合目標與 59／60、39／40、69／70 邊界測試。 |
| 房主選擇 Red | `618acd6` | `:finish` 尚不存在，API 測試預期失敗並得到 405。 |
| 房主選擇 Green | `e711197` | 新增 host-only、CSRF、version、idempotency 的 `FINISH_NOW／CONTINUE`。 |
| 自動結局敘事 Red | `b83ba9a` | 最終回合仍只有 narrator entry，缺少 ending entry。 |
| 自動結局敘事 Green | `f62dfc2` | 最終回合自動產生 deterministic ending narrative。 |
| Refactor | `6d02210` | 抽出共用完成流程，保持測試全綠。 |
| 前端合約 Red | `aeafcd6` | use case、adapter 與 ViewModel 的 5 項新斷言因功能不存在而失敗。 |
| 前端合約 Green | `6d21168` | 串接 finish endpoint 並提供結局 ViewModel。 |
| 頁面控制 Red | `ca89fe3` | 頁面缺少完成控制與 `handleFinish`，2 項斷言失敗。 |
| 頁面控制 Green | `c3039fb` | 加入正式進度／危機 meter、房主選擇與結局區塊。 |

每個 Red commit 都只含測試，且失敗原因是目標 production 行為尚不存在；production 實作只在後續 Green commit 出現。

## 敏感度測試

以下 mutation 均先讓測試失敗，再還原且未提交：

1. 將部分成功下限由 `60` 改為 `62`：60% 邊界測試由預期 `PARTIAL_SUCCESS` 變成 `FAILURE`。
2. 錯誤允許 `COLLECTING_ACTIONS` 呼叫 finish：無效狀態 API 測試由預期 409 變成 200。
3. 前端錯誤允許 `REWRITE_ENDING`：`FinishGame` allowlist 測試未拋出預期例外。

這證明測試會因核心規則、狀態授權與前端輸入邊界遭破壞而失敗，而不是只為現有實作背書。

## 最終自動測試

- Backend：`28 passed`。
- Frontend：`35 passed`。
- Backend 另有一項既有 `StarletteDeprecationWarning`，不影響測試結果；後續依相依套件升級工作處理。

## Browser 整合驗證

以 `127.0.0.1:8765` 啟動 FastAPI 同源頁面並確認：

- 頁面標示「本機 FastAPI 模式」，房間資料由 `/api/v1/rooms/current` 載入。
- 正式進度與正式危機百分比已顯示。
- `completionControls` 與 `endingPanel` 均存在；目前未達條件時正確保持隱藏。
- 1280×720 viewport 沒有水平溢出。
- Browser Console：`0 errors`。
- 驗證完成後已關閉分頁並停止 8765 暫時伺服器。

## 尚未涵蓋

- 三個獨立瀏覽器 session 的多人完整 E2E。
- polling、取消／離線錯誤狀態與 session expiry。
- PostgreSQL restart persistence 與真實 LLM adapter。
- 任何 AWS 部署或計費資源。
