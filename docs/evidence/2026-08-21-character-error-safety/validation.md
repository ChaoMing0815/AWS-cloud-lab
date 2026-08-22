# 角色儲存錯誤安全化驗證摘要

- Scope／risk／upstream：R2 玩家可見錯誤與資訊揭露；依 `screen-states.md` Unexpected error 規則及 8/20 公開試玩 finding。
- Baseline：Frontend `85 passed`；工作樹與遠端原先一致。
- Red commit：`6d3c8fe`。
- Red verification：targeted `1 passed, 1 failed`；失敗精確證明未知 `TypeError.message` 被直接顯示。
- Green commit：`49aa5dc`。
- Targeted verification：角色儲存錯誤 tests `3 passed`。
- Full regression：Frontend `88 passed`。
- Positive：已正規化的 `ApiError`／`DomainError` 仍顯示可修正訊息。
- Negative：未知 JavaScript exception 只顯示角色儲存專屬安全訊息，不含 `TypeError` 或原始內容。
- State：失敗保留角色輸入與 canonical room，並解除 submitting 狀態。
- Sensitivity：暫時恢復直接顯示 `error.message` 後 targeted test 如預期失敗；mutation 已還原，targeted tests 重回全綠。
- Browser／AWS：本 slice 未部署、未呼叫 AWS；Browser gate 留到 release gate。
- Rollback／residual risk：可回復 `49aa5dc`；刪房 direct catch 與其他分頁 `404` polling lifecycle 留待下一個獨立 slice。
