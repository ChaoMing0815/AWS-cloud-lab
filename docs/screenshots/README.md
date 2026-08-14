# 截圖清單

本目錄用來保存期末專題需要提交或展示的 AWS 截圖。

> ADR-0001 已將主題改為多人 AI 文字 RPG；下方 WordPress 檔名與項目仍待遷移，不得視為最新完成定義。

建議檔名使用階段與內容命名，例如：

```text
phase0-budget-alarm.png
phase1-vpc-overview.png
phase1-public-private-subnets.png
phase1-ec2-wordpress.png
phase1-rds-private.png
phase1-security-groups.png
phase1-wordpress-success.png
phase3-cloudwatch-dashboard.png
phase5-ssm-session-manager.png
phase5-ssm-run-command.png
```

## 必備截圖

### 目前候選部署帳號（2026-08-10 新帳號）

- [x] Free plan 狀態：[`phase0-new-account-free-plan.png`](phase0-new-account-free-plan.png)
- [x] 每月 `US$1.00` Budget：[`phase0-new-account-budget.png`](phase0-new-account-budget.png)
- [x] Root MFA 與無 Root Access Key：[`phase0-new-account-root-mfa.png`](phase0-new-account-root-mfa.png)
- [x] Root／`ming-dev` MFA：[`phase0-new-account-root-and-iam-mfa.png`](phase0-new-account-root-and-iam-mfa.png)
- [x] `ming-dev` Access／API／SSH keys 均為 0：[`phase0-ming-dev-zero-keys.png`](phase0-ming-dev-zero-keys.png)
- [x] `AWSFinalProjectDevelopers` 初始政策：[`phase0-ming-dev-group-policies.png`](phase0-ming-dev-group-policies.png)
- [x] `ming-dev` Billing 唯讀與當月 `USD 0.00`：[`phase0-ming-dev-billing-zero.png`](phase0-ming-dev-billing-zero.png)
- [x] Batch 0 Free plan 即時狀態：[`phase0-tier0-batch0-account-plan.png`](phase0-tier0-batch0-account-plan.png)
- [x] Free plan 結束日與剩餘天數：[`phase0-tier0-batch0-free-plan-expiration.png`](phase0-tier0-batch0-free-plan-expiration.png)
- [x] Credits 精確餘額、狀態與到期日：[`phase0-tier0-batch0-credits-summary.png`](phase0-tier0-batch0-credits-summary.png)／[`phase0-tier0-batch0-credits-detail.png`](phase0-tier0-batch0-credits-detail.png)
- [x] Budget 基本狀態與本月實際支出：[`phase0-tier0-batch0-budget-status.png`](phase0-tier0-batch0-budget-status.png)
- [x] Budget 告警清單：[`phase0-tier0-batch0-budget-alert-list.png`](phase0-tier0-batch0-budget-alert-list.png)
- [x] Budget 告警門檻與 Email subscriber 已由使用者在 Console 確認；Email 不入庫
- [x] Cost Explorer 可見性與 2026-02-01 至 2026-07-31 零成本：[`phase0-tier0-batch0-cost-explorer-visibility.png`](phase0-tier0-batch0-cost-explorer-visibility.png)
- [x] 2026 年 8 月本月至今成本摘要：[`phase0-tier0-batch0-current-month-cost.png`](phase0-tier0-batch0-current-month-cost.png)
- [x] 2026 年 8 月本月至今 7 個服務的成本明細：[`phase0-tier0-batch0-current-month-service-breakdown.png`](phase0-tier0-batch0-current-month-service-breakdown.png)
- [x] 未建立 AWS Organization：[`phase0-tier0-batch0-no-organization.png`](phase0-tier0-batch0-no-organization.png)
- [x] Tokyo 候選盤點 Region：[`phase0-tier0-batch0-region-tokyo.png`](phase0-tier0-batch0-region-tokyo.png)
- [x] Tokyo RDS 無資料庫資源：[`phase0-tier0-batch0-rds-tokyo-empty.png`](phase0-tier0-batch0-rds-tokyo-empty.png)
- [x] Tokyo Amazon Bedrock Model catalog：[`phase0-tier0-batch0-bedrock-tokyo-catalog.png`](phase0-tier0-batch0-bedrock-tokyo-catalog.png)
- [x] Tokyo VPC dashboard：[`phase0-tier0-batch0-vpc-dashboard-tokyo.png`](phase0-tier0-batch0-vpc-dashboard-tokyo.png)／[`phase0-tier0-batch0-vpc-dashboard-tokyo-zero-resources.png`](phase0-tier0-batch0-vpc-dashboard-tokyo-zero-resources.png)
- [x] CloudTrail 非唯讀 onboarding 事件：[`phase0-tier0-batch0-cloudtrail-write-events.png`](phase0-tier0-batch0-cloudtrail-write-events.png)
- [x] IAM bootstrap 與最終 6 份 group policies：[`phase0-iam-bootstrap-create-complete.png`](phase0-iam-bootstrap-create-complete.png)／[`phase0-iam-group-policies-final.png`](phase0-iam-group-policies-final.png)
- [x] Tier 0 network change set 與建立完成：[`phase0-tier0-network-change-set.png`](phase0-tier0-network-change-set.png)／[`phase0-tier0-network-create-complete.png`](phase0-tier0-network-create-complete.png)
- [x] Private DB local-only route 與 DB ingress：[`phase0-tier0-private-db-route.png`](phase0-tier0-private-db-route.png)／[`phase0-tier0-db-sg-ingress.png`](phase0-tier0-db-sg-ingress.png)
- [x] Default egress 發現、修正 change set 與更新完成：[`phase0-tier0-db-sg-default-egress-detected.png`](phase0-tier0-db-sg-default-egress-detected.png)／[`phase0-tier0-network-egress-fix-change-set.png`](phase0-tier0-network-egress-fix-change-set.png)／[`phase0-tier0-network-update-complete.png`](phase0-tier0-network-update-complete.png)
- [x] App／DB final egress：[`phase0-tier0-app-sg-egress-final.png`](phase0-tier0-app-sg-egress-final.png)／[`phase0-tier0-db-sg-egress-final.png`](phase0-tier0-db-sg-egress-final.png)
- [x] Tier 0 private RDS 兩項資源 change set（尚未 Execute）：[`phase0-tier0-rds-change-set.png`](phase0-tier0-rds-change-set.png)

### 歷史舊帳號（2026-08-07）

舊帳號的 Budget、Root、Organizations、CloudTrail 與 IAM Identity Center 截圖已於 2026-08-10 全部清除，避免與目前候選部署帳號混淆。事故原因與矯正措施只保留在 `docs/evidence/2026-08-07-*` 文字紀錄；不得把它們當成目前 AWS 狀態或最終報告證據。
- [ ] IAM Identity Center group、permission set 與 account assignment（遮罩 Email 與帳號識別資訊）
- [ ] AWS CLI SSO 登入與 caller identity（不得顯示 credential）
- [ ] 專題 IAM role trust policy 與 permissions policy
- [ ] VPC overview
- [ ] Public/private subnets
- [ ] EC2 位於正確 VPC 與 subnet
- [ ] RDS 位於 private subnet
- [ ] Security Group 規則
- [ ] WordPress 成功部署畫面
- [ ] WordPress 發文成功與資料持久保存

帳號／Region 的狹窄標頭截圖因遮罩影響可讀性未納入；新帳號 Region 尚待下次 AWS 唯讀盤點重新驗證。

## 加分截圖

- [ ] CloudWatch Dashboard
- [ ] CloudWatch Alarm
- [ ] SSM Session Manager
- [ ] SSM Run Command
- [ ] AI 維運 Agent 分析結果
- [ ] GitHub Actions pipeline
