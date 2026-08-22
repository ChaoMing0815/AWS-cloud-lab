# 世界生成回合上限保留驗證摘要

- Scope／risk／upstream：R2 可觀察 UI state；依 MVP Spec 5.2 與 8/20 公開試玩 finding。
- Baseline：Frontend `90 passed`。
- Red commit：`28f0127`。
- Red verification：targeted `0 passed, 1 failed`；房主選擇 `8` 後生成草稿實際回復為 `6`。
- Green commit：`8a27aa4`。
- Affected verification：world generation UI／use case／HTTP adapter `21 passed`。
- Full regression：Frontend `91 passed`。
- Positive：生成成功後保留房主尚未確認的回合上限，canonical world 草稿與剩餘次數仍正常更新。
- Boundary：未在生成 API 提前保存回合上限；正式確認世界仍由既有 `ConfirmWorld` contract 寫入 canonical state。
- Regression guard：生成 pending／安全錯誤與既有草稿保留行為維持全綠。
- Sensitivity：暫時改回 canonical `6` 後 targeted test 如預期失敗；mutation 已還原並重跑全綠。
- AWS／residual risk：Agent 未操作 AWS；使用者回報 RDS 為 `Stopping`。Safari 與 release Browser gate 尚待短時 AWS window。
