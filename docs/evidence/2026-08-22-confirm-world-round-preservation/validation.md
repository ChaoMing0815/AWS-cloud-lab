# 世界確認錯誤後回合選擇保留驗證摘要

- 日期：2026-08-22
- 風險：R2，可觀察 UI form state
- Green commit：`9ff0506`
- AWS／Browser：`9ff0506` 已隨 `tier0-20260822-de49944` 部署；Batch 10B zero-model Browser re-gate 發現後續 DRAFT polling 仍會覆寫選項。整段驗證未呼叫 Bedrock。

## Red

- 既有 confirm `422` 測試改以房主已選 `8`、canonical draft 仍為 `6` 的真實邊界執行。
- `run()` 的 finally render 將表單重設為 canonical `6`，targeted test 以 `6 !== 8` 正確失敗。

## Green

- `handleConfirmWorld()` 在送出前保存目前 `maxRoundsInput`。
- 只有確認失敗時才在 render 完成後恢復原選項；成功時仍接受 Backend 回傳的 canonical room，不覆寫正式資料。
- 欄位錯誤訊息、`aria-invalid` 與其他草稿輸入行為維持不變。

## Verification

- Targeted confirm `422`：`1 passed`。
- Affected world-generation／confirmation suite：`4 passed`。
- Frontend regression：`92 passed`。
- 代表性 sensitivity：測試中的 render 明確把表單改回 canonical `6`；移除 Green restore guard 時，測試會再次失敗為 `6 !== 8`。

## Batch 10B AWS re-gate finding

- Release `tier0-20260822-de49944` checksum `OK`；application／public edge／renewal timer active、staging inactive，readiness／public HTTPS `200`，previous release 為 `tier0-20260822-8bb6bfc`。
- 新建匿名驗證房 `LRTPGC`，完整重新載入部署後前端；房主選 `8` 回合並以低於 Backend 長度限制的短欄位送出確認。
- API `422` 正確顯示 premise／objective／opening scene／core obstacle 欄位錯誤，但下一次 DRAFT polling render 又以 canonical draft `6` 覆寫選項。
- Batch 10B 依停止條件中止，原定 exactly one Bedrock 世界生成呼叫未使用。

## Polling follow-up TDD

- Red `8dc7592`：新增「DRAFT polling 不覆寫未確認回合上限」測試，精確失敗為 `'6' !== '8'`。
- Green `1940b8b`：`applyPolledRoom()` 只在 incoming room 仍為 DRAFT 時，於 render 前保存目前選項並於 render 後恢復；離開 DRAFT 時仍以 Backend canonical state 為準。
- Targeted `1 passed`；world-generation＋polling affected suite `16 passed`；Frontend regression `93 passed`。
- Red 本身為代表性 sensitivity：移除 polling restore 後立即回到 `'6' !== '8'`。

## Residual

- AWS active release `tier0-20260822-de49944` 尚未包含 polling Green `1940b8b`；需先 push／CI，再建立新的 checksummed release 才能重驗。
- 世界生成成功後的 `8` 回合保留已有獨立本機測試；Batch 10B 因 zero-model gate 失敗而停止，AWS exactly-one-call 驗證仍未執行。
