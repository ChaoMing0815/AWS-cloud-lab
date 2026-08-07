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

- [x] AWS Budget Alarm：[`phase0-zero-spend-budget-verified.png`](phase0-zero-spend-budget-verified.png)
- [x] Root MFA 與無作用中 Root Access Key：[`phase0-root-mfa-and-access-keys.png`](phase0-root-mfa-and-access-keys.png)
- [x] AWS Organizations management account：[`phase0-organizations-management-account.png`](phase0-organizations-management-account.png)
- [x] CloudTrail Root `ConsoleLogin`：[`phase0-cloudtrail-console-login.png`](phase0-cloudtrail-console-login.png)
- [x] IAM Identity Center 啟用前狀態：[`phase0-identity-center-before-enable.png`](phase0-identity-center-before-enable.png)
- [x] IAM Identity Center 單一區域最終設定審查：[`phase0-identity-center-single-region-review.png`](phase0-identity-center-single-region-review.png)
- [x] IAM Identity Center 啟用完成：[`phase0-identity-center-enabled.png`](phase0-identity-center-enabled.png)
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

## 內部稽核截圖

- [x] CloudTrail 完整寫入事件：[`phase0-cloudtrail-write-events.png`](phase0-cloudtrail-write-events.png)（保存 `CreateOrganization` 等事件；不作最終報告主圖）
- [x] Identity Center multi-Region KMS 成本警告：[`phase0-identity-center-multi-region-cost-warning.png`](phase0-identity-center-multi-region-cost-warning.png)（證明已辨識並避開非必要費用）
- [x] Identity Center 空白 group：[`phase0-identity-center-group-created-internal.png`](phase0-identity-center-group-created-internal.png)（Group ID 已遮蔽；僅供內部稽核）

帳號／Region 的狹窄標頭截圖因遮罩影響可讀性未納入；Region 已記錄為 Tokyo `ap-northeast-1`，後續可由服務總覽截圖一併佐證。

## 加分截圖

- [ ] CloudWatch Dashboard
- [ ] CloudWatch Alarm
- [ ] SSM Session Manager
- [ ] SSM Run Command
- [ ] AI 維運 Agent 分析結果
- [ ] GitHub Actions pipeline
