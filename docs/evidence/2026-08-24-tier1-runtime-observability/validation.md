# Tier 1 Batch 11B runtime observability 執行摘要

- 核准邊界：使用者核准 Batch 11B；由使用者透過 AWS Console／SSM 操作，未由 Agent 執行 AWS CLI、S3 讀取或 Bedrock 呼叫。
- CloudWatch Agent 安裝：SSM Distributor `AWS-ConfigureAWSPackage` 執行成功，單一 target、`0` error；實機 package 為 `amazon-cloudwatch-agent-1.300071.0b1720-1.aarch64`，control tool 與 repo config 均存在。
- 安裝後 preflight：`co-story.service=active`、安全 JSONL runtime path 尚不存在、CloudWatch Agent service 為 inactive，符合尚未啟用 collection 的預期狀態。
- 首次設定嘗試：腳本加入安全 JSONL runtime 設定並重啟 application 後，立即檢查 loopback `127.0.0.1:8000` 時得到 `curl (7) Could not connect`；腳本依停止條件執行 rollback，回報 `rollback=attempted`、`configure_result=7`。
- 停止點：失敗發生在 CloudWatch Agent 啟動與 CloudWatch log delivery 驗證之前，因此目前不得宣稱安全 log stream、metric filter 或 runtime alarm path 已通過。
- Rollback audit：單次唯讀 SSM Session 確認 `co-story.service=active`、runtime env 已移除 `CO_STORY_APPLICATION_LOG_PATH`、`application.jsonl=absent`、CloudWatch Agent service 仍為 `inactive`；不需讀取 service failure journal，production 已恢復且沒有啟用 log collection。
- Health document 修正：依 R3 嚴格 TDD 將固定路徑修正為 `/api/v1/live`、`/api/v1/ready`；Red `dcd8efd`、Green `529d223`，targeted `5 passed`、Tier 1 affected `15 passed`、Backend `330 passed, 8 skipped`，代表性舊 `/live` mutation 會被測試攔截。AWS 上仍是舊版本；完成 Change Set 更新前禁止執行。
- Restart wait 評估：首次失敗與 restart 後立即單次 curl 相符，但既有證據不足以排除其他啟動原因。下一次設定命令應以固定總期限、固定間隔輪詢 `/api/v1/ready`；只有 service active 且 readiness 成功才啟動 Agent，逾時即 rollback 並停止。
- 成本：本次新增的是既有 EC2 上的 Agent package；尚無 log delivery 證據。既有 Log Group／custom metric／Alarm 的費用邊界不變。

結果：**PARTIAL／ROLLBACK VERIFIED**。下一步先以 Change Set 更新 `CoStoryHealthCheck`，確認新版本後才可執行；runtime 設定重試須使用 bounded readiness wait，且仍不得直接沿用首次命令。
