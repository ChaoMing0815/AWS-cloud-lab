# 世界確認錯誤後回合選擇保留驗證摘要

- 日期：2026-08-22
- 風險：R2，可觀察 UI form state
- Green commit：`9ff0506`
- AWS／Browser：本切片未部署、未操作 AWS、未呼叫 Bedrock；finding 來源為 Batch 10A Browser gate。

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

## Residual

- AWS active release `tier0-20260822-8bb6bfc` 尚未包含 `9ff0506`；若要做 Browser re-gate，需建立後續 release batch。
- 世界生成成功後的 `8` 回合保留已有獨立本機測試；AWS E2E 仍未呼叫 Bedrock 驗證。

