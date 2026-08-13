# WorldDraft 確認契約與欄位錯誤驗證摘要

- Scope／risk／upstream source：R2；`CURRENT.md` 記錄的本機試玩阻斷、既有 `ConfirmWorldRequest` schema 與 Web API boundary。
- Backend Red：`d04dd92`；預設 Mock 生成的草稿直接確認得到預期外的 `422`。
- Backend Green：`204a5c5`；Mock `premise` 延長至現有 schema 合法範圍，未放寬 API 驗證。
- Frontend Red：`88d5478`、`6096542`；FastAPI `detail` 尚未轉為欄位錯誤，表單也尚無可存取的錯誤訊息區。
- Frontend Green：`fafea8a`；只轉譯已知結構化 validation type，並對世界表單的對應欄位設 `aria-invalid` 與訊息。
- Targeted：World generation API `14 passed`；Frontend adapter／world UI／markup `20 passed`。
- Full regression：Backend `239 passed, 8 skipped`；Frontend `80 passed`。
- Browser：重啟載入最新 commit 的本機 `127.0.0.1:8000` 後，3 關鍵字生成的 `premise` 為 58 字；確認世界成功進入 Lobby。
- Negative／boundary：短於 50 字的 generated `premise` 會使確認 API 回傳 `422`；422 僅顯示安全的本地化欄位提示。
- Sensitivity：暫時將 Mock `premise` 還原為過短字串，新增確認契約測試如預期失敗；已立即還原並重跑全套。
- Rollback：回復上述 Green commits；本批沒有 migration、network、secret 或 AWS 狀態變更。
- Residual risk：下一個 production-parity gate 仍需驗證正式設定與 Linux runtime。
