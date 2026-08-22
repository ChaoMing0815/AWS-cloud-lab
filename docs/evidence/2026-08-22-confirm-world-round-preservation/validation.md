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

## Batch 10C AWS re-gate

- Release `tier0-20260822-c5c1541` 由 PR #6 exact merge commit 建置；S3 exact objects `2`、EC2 checksum `OK`。部署後 application／public edge／renewal timer active、staging inactive，readiness／public HTTPS `200`，previous release 為 `tier0-20260822-de49944`。
- 同一匿名驗證房 `LRTPGC` 完整 reload 後，房主選 `8` 回合並送出低於 Backend 長度限制的短欄位；API `422` 正確顯示 field errors，返回當下仍為 `8`。
- 等待 `4.2` 秒、跨過至少一個 `3` 秒 polling 週期後，回合上限仍為 `8`；zero-model gate 通過。
- 只執行 exactly one benign Bedrock 世界生成：關鍵字為匿名虛構內容「雨夜／山村／風車」，生成成功，剩餘次數由 `2` 變 `1`，表單取得完整 canonical world draft。
- 生成後再等待 `4.2` 秒，回合上限仍為 `8`；世界生成前後與後續 polling 的 state-preservation gate 全數通過。未重試 Bedrock。
- 新 finding：先前 `422` 的 field error／`aria-invalid` 在成功生成有效草稿後仍殘留。這不影響生成結果、回合選項或後續再次確認時的清除行為，但會造成誤導，列為後續小型 UX TDD slice。

## Residual

- AWS active release `tier0-20260822-c5c1541` 已包含 polling Green `1940b8b`，zero-model 與 exactly-one-call AWS Browser gates 均已通過。
- 成功生成世界後仍殘留先前 field errors；尚未執行後續 UX 修正。
