# Tier 1 最小可觀測性與 SSM Gap Analysis

- 狀態：Proposed；僅完成 repo-local 分析，未核准或執行 AWS change batch。
- 日期：2026-08-22。
- 目標：依甘特圖縮減原則，交付一條安全 application log→metric→alarm，以及一個受限 SSM Run Command 檢查流程。

## 已具備

- FastAPI 已以 `co_story.request` 輸出單行 JSON：只含 generated request ID、method、path、status、latency；query、cookie、body 與外部 request ID 不入 log。
- Storyteller failure log 只含 operation 與 allowlisted failure code。
- EC2 以 systemd 執行 application，SSM Agent／Session Manager 已在實機驗證，且沒有 public SSH。
- EC2、RDS、Bedrock 的 native metrics 已在四玩家公開試玩留下證據。

## 缺口

- Application logs 目前只留在 host logging path，沒有 CloudWatch Log Group、7 天 retention 或 agent collection config。
- `AWSFinalProjectAppRole` 只有 SSM core 與 bounded Bedrock runtime，沒有指定 log group 的 CloudWatch Logs write 權限。
- 沒有 JSON `5xx` metric filter、alarm、事件時序或 recovery evidence。
- 沒有專題限定的 SSM Command document；不得讓一般 operator 使用可執行任意 shell 的 `AWS-RunShellScript`。

## 建議的第一個嚴格 TDD 切片

1. 建立安全的 production JSONL file sink，只接收 `co_story.request` 與 `co_story.storyteller`；不收自由輸入或 Uvicorn raw access log，並限制本機檔案大小／rotation。
2. 建立 CloudWatch Agent file collection config，僅讀取該 JSONL file，送到固定 `/co-story/tier1/application` Log Group；retention `7` 天。
3. AppRole 只新增該 log group／stream 的 `logs:CreateLogStream`、`logs:DescribeLogStreams`、`logs:PutLogEvents`；不授予 `CloudWatchAgentServerPolicy` 全域權限。
4. 建立 JSON filter `{ $.status >= 500 }`、單一 `Application5xx` metric 與 `>= 1 / 1 minute` alarm；第一批不加入 SNS Email、Lambda 或自動修復。
5. 建立沒有自由文字 command parameter 的 `CoStoryHealthCheck` SSM document，只執行 service active、loopback live／ready；target 限定既有 `Project=co-story`、`Tier=0` instance。
6. Incident gate 留到短時 AWS window：RDS stopped 時 readiness `503`→log／alarm→人工判讀→人工核准啟動 RDS→readiness `200`。不得為測試呼叫 Bedrock。

## 成本、安全與停止條件

- 計費面只有 CloudWatch Logs ingestion／storage、custom metric 與 alarm；AWS 寫入前須以 Tokyo 價格完成 bounded estimate、Budget／credits／principal 重新確認。
- Log Group 預先建立，禁止 app role 建立任意 group；retention 固定 7 天，測試後不保留高流量 log。
- Run Command history 不放 secret、DB URL、cookie、token 或任意 shell；AWS 官方指出可使用任意 `AWS-*` command document 等同節點管理員能力，故排除。
- IAM scope、resource count、估價或外部通知超出本文件即停止並重新核准 envelope。

官方依據：[CloudWatch Agent](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Install-CloudWatch-Agent.html)、[Agent regular-file configuration](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Agent-Configuration-File-Details.html)、[Metric filters](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html)、[Run Command security warning](https://docs.aws.amazon.com/systems-manager/latest/userguide/walkthrough-cli.html)。
