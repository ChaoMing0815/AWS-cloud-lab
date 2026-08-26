# 手動與自動部署效率量測方法

- 狀態：量測方法已定義；尚無足夠 AWS 自動部署樣本，不填造數據。
- 比較單位：同一個可部署 commit 從「開始交付」到 public `/live`、`/ready` 均驗證成功。
- 手動樣本：下一次 container bootstrap／manual release 由操作人記錄開始、artifact ready、SSM release start、完成 epoch、人工互動次數與失敗次數。
- 自動樣本：`tier3-delivery-metrics-<run-id>` GitHub artifact；成功或失敗皆保留 30 天。

## 指標

| 指標 | 手動部署 | 自動部署 |
| --- | --- | --- |
| End-to-end 秒數 | 第一個操作開始至 health gate | 首個 measurement job 至 workflow completion |
| Build／scan 秒數 | 本機 build／scan 開始至 artifact ready | `deploy_start` 至 `artifact_ready` |
| Release attempt 秒數 | SSM release start 至完成／失敗 | `release_start` 至 `completed` |
| 人工互動數 | Console／上傳／指令／核准逐次計數 | 固定為 dispatch＋production approval，共 2 次 |
| 成功率 | verified runs ÷ all runs | verified artifacts ÷ all artifacts |
| Rollback 秒數 | failure detected 至 previous health restored | failure detected 至 previous health restored |

## 報告計算

至少保存 1 次受控 manual bootstrap 與 3 次 automatic release；分別報告樣本數、median 與每次原始值。`節省秒數 = manual median − automatic median`；`改善率 = 節省秒數 ÷ manual median × 100%`。若 manual 只有 1 次，必須標示為 baseline case study，不宣稱統計顯著。

Approval queue time 與 automation execution 分開報告，避免把人員等待誤算成機器執行成本。歷史 S3／SSM release 因沒有一致時間戳，只作流程與錯誤案例，不回推分鐘數。

Artifact 僅保存 commit SHA、GitHub run ID、狀態、epoch、duration 與互動數；不得包含 account ID、instance ID、role ARN、SSM output、URL、token 或 secret。
