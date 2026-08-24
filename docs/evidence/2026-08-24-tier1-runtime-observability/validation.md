# Tier 1 Batch 11B runtime observability 執行摘要

- 核准邊界：使用者核准 Batch 11B；由使用者透過 AWS Console／SSM 操作，未由 Agent 執行 AWS CLI、S3 讀取或 Bedrock 呼叫。
- CloudWatch Agent 安裝：SSM Distributor `AWS-ConfigureAWSPackage` 執行成功，單一 target、`0` error；實機 package 為 `amazon-cloudwatch-agent-1.300071.0b1720-1.aarch64`，control tool 與 repo config 均存在。
- 安裝後 preflight：`co-story.service=active`、安全 JSONL runtime path 尚不存在、CloudWatch Agent service 為 inactive，符合尚未啟用 collection 的預期狀態。
- 首次設定嘗試：腳本加入安全 JSONL runtime 設定並重啟 application 後，立即檢查 loopback `127.0.0.1:8000` 時得到 `curl (7) Could not connect`；腳本依停止條件執行 rollback，回報 `rollback=attempted`、`configure_result=7`。
- 停止點：失敗發生在 CloudWatch Agent 啟動與 CloudWatch log delivery 驗證之前，因此目前不得宣稱安全 log stream、metric filter 或 runtime alarm path 已通過。
- 未決狀態：rollback 是否已恢復 `application=active`、移除 runtime env 設定並維持 Agent inactive，仍需下一次 SSM Session 只讀確認。`curl (7)` 可能是 restart 後 readiness race，也可能是 application 啟動失敗；取得 service 狀態前不定因。
- 額外 repo 缺口：已部署的 `CoStoryHealthCheck` 文件仍檢查 `/live`、`/ready`，實際 API route 為 `/api/v1/live`、`/api/v1/ready`。該文件尚未執行；必須先依嚴格 TDD 修正並透過 Change Set 更新，再做 Run Command 實機驗證。
- 成本：本次新增的是既有 EC2 上的 Agent package；尚無 log delivery 證據。既有 Log Group／custom metric／Alarm 的費用邊界不變。

結果：**PARTIAL／STOPPED SAFELY**。下一步先做 rollback 狀態的唯讀確認，不重跑設定；確認 production service 正常後，再針對啟動等待機制做 repo-local TDD 修正。
