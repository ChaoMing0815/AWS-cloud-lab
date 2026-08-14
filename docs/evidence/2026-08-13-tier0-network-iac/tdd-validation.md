# Tier 0 network IaC 驗證摘要

- Scope／risk／upstream source：R3；Tier 0 AWS deployment plan 的 VPC、公私 subnet、route 與 Security Group 邊界。
- Red：`1dd7869`；三項 topology／route／SG contract 因 template 不存在而預期失敗。
- Green：`f4ff321`；新增僅含 network 的 CloudFormation template，不含 EC2、RDS、IAM、Secrets 或 Bedrock 資源。
- Local verification：初始 network contract `3 passed`、YAML parse 成功；實機發現 default egress 後的修正版與 IAM contracts 合計 `8 passed`，完整 Backend `247 passed, 8 skipped`。
- Negative／sensitivity：暫以 CIDR 取代 DB 的 App SG reference，DB ingress contract 如預期失敗；已立即還原。
- Security boundary：僅 public app subnet 有 IGW default route；兩個 DB subnets 不配 public IP、無 NAT；不開 `22`／`8000`；DB `5432` 僅信任 App SG。
- AWS result：2026-08-14 經人工核准後由使用者在 Console 建立並更新 `co-story-tier0-network`；全程未呼叫 AWS CLI。實際部署與 egress 修正證據見 [`2026-08-14-tier0-network-deployment`](../2026-08-14-tier0-network-deployment/validation.md)。
- Rollback／residual risk：刪除 `co-story-tier0-network` stack 可回復 network；RDS、EC2、Bedrock 與真實應用仍未建立。
