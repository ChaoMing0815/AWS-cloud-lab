# 截圖清單

本目錄用來保存期末專題需要提交或展示的 AWS 截圖。

> 本頁是實際截圖資產索引，不是工作 backlog。依 [ADR-0008](../decisions/0008-fix-final-delivery-scope.md)，本次交付止於 production 組件化與自動部署；Tier 4／5 不由截圖缺項推導為待辦。下方 WordPress 檔名只保留歷史命名，不是產品要求。

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
- [x] Tier 0 RDS 建立失敗診斷：[`空白 network parameters`](phase0-tier0-rds-parameter-validation-failure.png)／[`EngineVersion 使用 Console 描述而非 API 值`](phase0-tier0-rds-engine-version-failure.png)
- [x] Tier 0 private RDS 建立完成與 Available：[`CloudFormation events`](phase0-tier0-rds-create-complete-events.png)／[`stack`](phase0-tier0-rds-stack-create-complete.png)／[`RDS summary`](phase0-tier0-rds-available-summary.png)
- [x] Tier 0 private RDS 最終設定與 network boundary：[`configuration`](phase0-tier0-rds-configuration.png)／[`internet access disabled`](phase0-tier0-rds-internet-access-disabled.png)／[`DB SG rules`](phase0-tier0-rds-security-group-rules.png)
- [x] Tier 0 EC2＋SSM change set 與建立完成：[`change set`](phase0-tier0-compute-change-set.png)／[`stack`](phase0-tier0-compute-stack-create-complete.png)／[`events`](phase0-tier0-compute-create-complete-events.png)
- [x] SSM managed node Online 與免 SSH Session Manager：[`managed node`](phase0-tier0-ssm-managed-node-online.png)／[`session validation`](phase0-tier0-ssm-session-validation.png)

### 歷史舊帳號（2026-08-07；封存、不適用）

舊帳號的 Budget、Root、Organizations、CloudTrail 與 IAM Identity Center 截圖已於 2026-08-10 全部清除，避免與目前部署帳號混淆。事故原因與矯正措施只保留在 `docs/evidence/2026-08-07-*` 文字紀錄；不得把已清除的 IAM Identity Center、VPC、RDS、Security Group 或 WordPress 截圖當成目前待補項、AWS 狀態或最終報告證據。

帳號／Region 的狹窄標頭截圖因遮罩影響可讀性未納入；目前帳號與 Region 已確認，除非 AWS change envelope 擴張，不重複盤點。

## 歷史加分截圖提示

CloudWatch Dashboard／Alarm、SSM Session Manager／Run Command、AIOps 分析與 GitHub Actions pipeline 均已有 milestone evidence。最終只需從既有安全資產挑選可讀、已遮罩的代表畫面，不將本段當成重新執行 AWS 驗證的清單。
