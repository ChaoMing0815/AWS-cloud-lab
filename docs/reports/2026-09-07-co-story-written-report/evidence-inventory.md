# 可用檔案與 sanitized evidence inventory

## 可直接作為正文依據

| 主題 | canonical 檔案 | 可支持的敘述 |
|---|---|---|
| 帳號、成本與初始安全基線 | `docs/evidence/2026-08-13-tier0-batch0-console-inventory/inventory-summary.md`、`docs/evidence/2026-08-07-p0-1-account-security/inventory-summary.md` | Tokyo、Free plan／credits、Budget、無長期金鑰與 Organizations 風險；只寫去識別化結果 |
| VPC 與公私網路 | `docs/evidence/2026-08-14-tier0-network-deployment/validation.md`、`docs/evidence/2026-08-13-tier0-network-iac/tdd-validation.md` | public app subnet、private DB subnets、路由與 SG 最小開放 |
| RDS PostgreSQL | `docs/evidence/2026-08-14-tier0-rds-iac/tdd-validation.md` | private、Single-AZ、加密、managed master password、Change Set 與 rollback |
| EC2／IAM／SSM | `docs/evidence/2026-08-15-tier0-compute-iac/tdd-validation.md`、`docs/evidence/2026-08-23-tier1-ssm-health-check/validation.md` | public Web compute、EC2 role、IMDSv2、Session Manager、免 SSH 維運 |
| CloudFormation／Change Set | `docs/evidence/2026-08-13-tier0-network-iac/tdd-validation.md`、`docs/evidence/2026-08-26-tier3-control-plane/validation.md` | template-first、Add-only Change Set、無 replacement、IAM/OIDC/ECR/SSM control plane |
| CloudWatch／AIOps | `docs/evidence/2026-08-25-tier1-completion/validation.md`、`docs/evidence/2026-08-24-tier1-aiops-agent/validation.md` | logs、metrics、dashboard、alarm、Nova Lite 分析建議與 human approval |
| SQS／DLQ／Publisher／Workers | `docs/evidence/2026-08-29-tier2-worker-runtime-deployment/validation.md`、`docs/evidence/2026-08-29-tier2-publisher-service/validation.md`、`docs/evidence/2026-08-31-tier2-web-async-activation/validation.md` | queue idle gate、Publisher、兩台 private Worker、async producer、rollback 邊界 |
| Bedrock Nova Lite | `docs/evidence/2026-09-05-bedrock-tooluse-hotfix/validation.md`、`docs/evidence/2026-08-18-tier0-bedrock-smoke/validation.md` | production storyteller、受控 tool schema、模型失敗邊界；不得稱為 RAG |
| Docker／ECR／OIDC／Actions／Trivy | `docs/evidence/2026-08-26-tier3-delivery/validation.md`、`docs/evidence/2026-08-31-tier3-production-release/validation.md` | immutable image、fail-closed scan、OIDC、人工 approval、digest rollback |
| Support Widget boundary | `docs/evidence/2026-09-01-support-pixel-widget/validation.md`、`docs/evidence/2026-09-01-ui-support-production-release/validation.md` | cited／unsupported 查詢、Player-only `local_draft_only`、人工確認、不外送 |
| 產品與測試治理 | `docs/product/source-of-truth.md`、`docs/testing-strategy.md`、`docs/governance/parallel-branch-boundaries.md` | 權威衝突處理、strict TDD、分支白名單、Agent 角色與限制 |

## 可重用 sanitized 資產

`docs/screenshots/` 中有對應 Change Set、RDS、EC2／SSM、CloudWatch、ECR／OIDC／IAM 的去識別化截圖；正文引用前仍需逐張確認沒有 account ID、完整 ARN、IP、endpoint、instance／subnet／SG ID、Email、token 或 secret。

## 排除來源

候選 v1.1.2 PPTX、TemporaryItems 原始截圖、未去識別化 Console 輸出，以及任何把 Route 53、CloudFront/CDN、ELB/ASG、SNS、App Runner、API Gateway、Lambda、SageMaker、DynamoDB、Step Functions、Bedrock Knowledge Bases／RAG 寫成已部署能力的資料，均不列入 current evidence。
