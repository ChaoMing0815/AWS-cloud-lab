# Tier 0 network IaC 驗證摘要

- Scope／risk／upstream source：R3；Tier 0 AWS deployment plan 的 VPC、公私 subnet、route 與 Security Group 邊界。
- Red：`1dd7869`；三項 topology／route／SG contract 因 template 不存在而預期失敗。
- Green：`f4ff321`；新增僅含 network 的 CloudFormation template，不含 EC2、RDS、IAM、Secrets 或 Bedrock 資源。
- Local verification：network contract `3 passed`、YAML parse 成功；完整 Backend `242 passed, 8 skipped`。
- Negative／sensitivity：暫以 CIDR 取代 DB 的 App SG reference，DB ingress contract 如預期失敗；已立即還原。
- Security boundary：僅 public app subnet 有 IGW default route；兩個 DB subnets 不配 public IP、無 NAT；不開 `22`／`8000`；DB `5432` 僅信任 App SG。
- AWS boundary：尚未呼叫 CloudFormation validate、plan、create 或任何 AWS CLI；這些需等 Tier 0 bounded change envelope 的人工核准。
- Rollback／residual risk：回復 Green commit 可移除未執行 template；真實 AZ、account、Region、resource names、費用、IAM、RDS 與 EC2 都尚未選定或建立。
