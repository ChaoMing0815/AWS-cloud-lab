# ADR-0007：採用 SQS 與兩台 private Story Worker

- 狀態：Accepted
- 日期：2026-08-28
- 決策 owner：整合 task／使用者
- 上游核准：剩餘 Credits USD 125.59；核准兩台 private Worker 與單一 NAT Gateway

## 背景

Tier 2 的本機 Web／Story Worker／Data contract、PostgreSQL durable job／result schema與production Bedrock Worker composition均已完成，但AWS仍只有public Web EC2與private RDS。Production保持`CO_STORY_RESOLUTION_MODE=sync`，尚未建立SQS、private Worker compute或玩家可見async flow。

課程對照要求至少三個AWS compute／EC2。既有public Web EC2加兩台private Worker EC2可直接展示三compute拓樸、queue解耦與單台instance故障替換；RDS繼續作為private Data authority。

## 決策

1. 建立一個新的private Worker subnet，`MapPublicIpOnLaunch=false`。
2. 以Auto Scaling Group固定維持兩台`arm64 t4g.micro` Worker；兩台均位於同一private subnet，不開inbound、不配置SSH key，維運只使用SSM。
3. 建立一個public NAT Gateway，讓private Worker以HTTPS存取SSM、ECR、Secrets Manager、CloudWatch、SQS與Bedrock；DB連線只允許Worker SG到既有DB SG的TLS PostgreSQL `5432`。
4. 建立一個SQS Standard Queue與一個DLQ；使用SSE-SQS、20秒long polling、180秒visibility timeout與`maxReceiveCount=3`。Queue policy拒絕非TLS傳輸。
5. PostgreSQL仍是Job／Room／Result的唯一權威。未來SQS message只攜帶`schema_version`與opaque `job_id`，Worker依`job_id`從RDS載入已清理snapshot；不把玩家文字、secret或DB credential放入message。
6. Web與Worker使用分離權限：Web只可向指定主Queue送信；Worker只可receive／delete／change visibility，不可送信或讀取任意Queue。Worker另使用限定ECR repository、runtime secret、Nova Lite＋Guardrail與Worker log group的權限。
7. Foundation只建立基礎資源與Docker host bootstrap，不啟動Worker application、不pull image、不切換Web到async。SQS adapter、visibility heartbeat、runtime deployment與玩家流程分批完成。

## 理由

- 兩台Worker可展示SQS競爭消費、水平擴充與單一EC2故障後由ASG補回。
- private subnet與無public IP比把Worker放在public subnet更符合Tier 2網段隔離。
- 單一NAT Gateway比一次建立多個interface endpoints更快完成課程Demo，且資源與費用容易由單一stack清理。
- SSE-SQS不需要新增customer KMS key與對應IAM／KMS API費用。
- SQS只作delivery signal，PostgreSQL fencing／idempotency／result inbox／completion outbox繼續處理at-least-once replay，不宣稱distributed exactly-once。

## 成本與限制

- 新增計費面：兩台`t4g.micro`、兩個8 GiB gp3 volume、NAT Gateway時數與處理流量、public IPv4、CloudWatch Logs；SQS按request計費。
- Change Set執行前必須用`ap-northeast-1` Pricing Calculator重新估算到Demo／清理日的增量費用，並由使用者核准該次cost ceiling。
- NAT Gateway只保留至Tier 2驗證完成；Demo後若不再需要，刪除整個foundation stack並確認NAT、EIP、ASG與volumes沒有殘留。
- 兩台Worker位於同一AZ，因此只降低單一instance故障風險，不提供AZ failure continuity。跨AZ Worker與第二個NAT不在本階段範圍。
- Worker HTTPS目前可經NAT前往任意destination；後續可用SQS、Bedrock、ECR、SSM、Logs與Secrets Manager VPC endpoints收斂，但不在本批建立。

## 分階段啟用

1. `worker-foundation`：CloudFormation、IAM、private network、SQS／DLQ、兩台空白Worker host。
2. `sqs-runtime`：repo-local SQS adapter、message schema、visibility heartbeat與Worker process deployment。
3. `worker-e2e`：AWS action→queue→Worker→Bedrock→RDS→result與負面權限／網路證據。
4. `async-activation`：獨立release把Web由精確`sync`切到`async`，再驗證`202`→polling→result與rollback。

任何階段失敗都不得提前進入下一階段；foundation成功不代表Tier 2或玩家可見async已完成。
