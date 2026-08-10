# 共演計劃：預計使用的 AWS 服務

本文件描述同一個產品由 Tier 0 累積演進至 Tier 5 的目標服務，不代表資源已建立。AWS 帳號、預算、估價與部署窗口未確認前，不建立計費資源。

## 分層服務清單

| 階段 | AWS 服務 | 用途與驗收重點 |
| --- | --- | --- |
| 共通治理 | AWS Budgets、Cost Explorer、CloudTrail Event history、IAM | 成本告警、費用盤點、操作稽核與最小權限；不建立長期 Access Key |
| Tier 0 | Amazon VPC、public/private subnet、Internet Gateway、Security Group | 公開 Web、私有資料層與最小網路規則 |
| Tier 0 | Amazon EC2、Amazon EBS | 執行可玩的 Web App 與 API；使用小型 instance，非 Demo 時停止 |
| Tier 0 | Amazon RDS for PostgreSQL | 依 ADR-0003 保存 Room aggregate；放在 private DB subnets，禁止 public access。仍待講師確認 Tier 0 題卡等價性 |
| Tier 0 | Amazon Bedrock | AI 故事主持人；使用 On-Demand、限制輸入輸出 token，不使用 Provisioned Throughput |
| Tier 0–1 | AWS Systems Manager | Session Manager、Run Command 與免 SSH 維運 |
| Tier 0–1 | Amazon CloudWatch | Application logs、EC2/RDS metrics、dashboard、alarm 與 incident 證據 |
| Tier 1 | Systems Manager Parameter Store | 保存非敏感設定；敏感值是否改用 Secrets Manager依實際需求決定 |
| Tier 2 | Amazon SQS、額外 EC2 或等價 compute | 將 Story Worker 從 Web/API 拆離，示範至少三個運算／服務元件與非同步處理 |
| Tier 3 | Amazon ECR、GitHub Actions OIDC | Container image、測試、build 與短期憑證自動部署 |
| Tier 4 | Amazon ECS 或 EC2 containers、Application Load Balancer（若需要） | 拆分 Lobby、Character、Turn、Rules、Story 等服務；展示服務邊界與故障隔離 |
| Tier 5 | Amazon S3、Bedrock、RDS PostgreSQL/pgvector 或核准的向量儲存 | Prompt 版本、RAG 知識庫、MCP 工具、多 Agent 與可觀測性 |

## 成本與安全邊界

- `RDS`、額外 EC2、ALB、ECS 等常駐資源，只在所屬 Tier 的建置與 Demo 窗口啟動；完成證據後立即停止或清除可回復資源。
- Tier 0 不建立 `NAT Gateway`；若 private workload 需要對外連線，先提出替代設計與估價再決定。
- EC2 不開 `0.0.0.0/0:22`，以 Systems Manager 維運。
- 人員使用 MFA 與短期登入；GitHub 使用 OIDC；應用程式使用 workload role，不保存 Access Key。
- Security Group 只開必要方向與 port；RDS 僅允許 application Security Group 存取。
- CloudWatch Logs 設定短期 retention，Bedrock 限制模型、上下文、回合與 token。
- 未經估價與明確核准，不使用 `EKS`、`OpenSearch Service`、Bedrock Provisioned Throughput、Customer managed KMS key 或多區域架構。

## 部署前必要關卡

- 確認可使用的 AWS 帳號、account plan、credits 與每階段可接受預算。
- 以 AWS Pricing Calculator 保存 EC2、RDS、Public IPv4、CloudWatch、Bedrock，以及後續 ALB/ECS 的估價證據。
- 由講師確認自製 FastAPI＋private PostgreSQL 是否可作為 Tier 0 Web／DB 分離的等價成果。
- 依已接受的 ADR-0003 使用 PostgreSQL repository；AWS RDS 只替換 endpoint／secret source，不改 application port。
- 每次寫入 AWS 前再次做 Billing、Budget、Region、principal 與既有資源唯讀盤點。

Tier 0 的精確網路、IAM、runtime、驗證與清理設計見 [`docs/architecture/tier0-aws-deployment-plan.md`](architecture/tier0-aws-deployment-plan.md)。

## 暫不採用

| 服務／功能 | 原因 |
| --- | --- |
| NAT Gateway | 固定成本較高，Tier 0 無必要；後續需先估價 |
| Amazon EKS | 專題時間與成本不適合；微服務先以 ECS 或 EC2 containers 展示 |
| Amazon OpenSearch Service | MVP/RAG 規模不足以合理化常駐叢集 |
| Bedrock Provisioned Throughput | Demo 流量低，優先 On-Demand |
| 長期 IAM Access Key | 改用 IAM role、SSO 或 GitHub OIDC 的短期憑證 |
