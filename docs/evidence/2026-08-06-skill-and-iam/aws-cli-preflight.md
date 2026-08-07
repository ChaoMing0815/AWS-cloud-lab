# AWS CLI 與 Console 前置盤點

- 盤點日期：2026-08-06
- AWS CLI：`aws-cli/2.36.8`
- CLI profiles：無
- CLI 預設 Region：未設定
- `AWS_*` 環境變數：無
- `aws sts get-caller-identity`：失敗，`NoCredentials`；未輸出任何 credential
- AWS Console：已開啟，但停在 AWS 登入頁
- AWS API 唯讀盤點：尚未執行；目前沒有可用的 SSO profile 或登入工作階段
- AWS 寫入：未執行

## 結論

目前無法安全確認 principal、account ID、Region、Identity Center、IAM、Budget、Root MFA、CloudTrail 或現有資源。完成 Console 登入與 MFA 後，先執行唯讀盤點；在盤點完成前不得建立 Identity Center assignment、permission set 或 IAM role。

## 費用提醒

IAM、IAM Identity Center 的基本設定本身通常不是本專題的主要計費來源；後續 EC2、RDS／其他資料層、NAT Gateway、ALB、CloudWatch Logs、Bedrock 與資料傳輸可能計費。任何基礎設施寫入前仍須驗證 Budget 狀態、當月成本與清理計畫。
