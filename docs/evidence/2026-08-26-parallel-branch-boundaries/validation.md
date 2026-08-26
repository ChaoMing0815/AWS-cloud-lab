# 平行分支權限治理驗證摘要

- Scope／risk／upstream source：R2 Git／CI boundary；依使用者要求隔離產品品質與 Tier 3 delivery 工作。
- Baseline：治理前沒有 branch policy、path checker 或 PR ownership gate。
- Red commit：`6a76daf`；targeted `5 failed`，均因必要治理資源尚不存在。
- Green commit：`b772116`。
- Registered branches：`codex/story-quality`、`codex/tier3-delivery`。
- Targeted verification：boundary＋既有 CI contract `7 passed`。
- Full Backend regression：`371 collected`、`363 passed`、`8 skipped`。
- Full Frontend regression：`94 passed`。
- Negative verification：unknown branch 預設 fail closed；兩分支的跨責任路徑與 protected paths 均回 exit `2`。
- Sensitivity：暫時停用 allowlist 拒絕後，兩個代表性測試失敗；mutation 已還原並重跑全綠。
- CI behavior：Pull request 對 registered branch 以 base/head SHA 計算 changed paths；其他既有 branch 不受此專案專用 gate 阻擋。
- AWS boundary：未執行 AWS CLI、S3 讀取、Bedrock 呼叫或 production deploy。
- Residual risk：worktree 隔離不能消除語意衝突；shared/protected files 仍只由整合 task 修改與最終 review。

## Storyteller adapter 權限修正

- 產品 task 回報原 policy 使用不存在的 `backend/co_story/**`，實際需要兩個 `backend/app/adapters` 檔案。
- Red `c56cb37` 精確證明兩個 adapter 均被拒絕；Green `de80a80` 只加入兩個檔案級白名單並移除錯誤 pattern。
- Targeted boundary／CI contract `7 passed`；Backend `363 passed, 8 skipped`；Frontend `94 passed`。
- Delivery、IaC、protected paths 的拒絕案例維持全綠；沒有開放 `backend/app/**`。
