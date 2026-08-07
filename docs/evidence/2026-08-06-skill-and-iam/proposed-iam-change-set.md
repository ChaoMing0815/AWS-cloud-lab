# IAM 預定變更集（等待唯讀盤點）

此文件是寫入前草案，不代表 AWS 已建立任何物件。

## Identity Center

- 確認或啟用 IAM Identity Center；啟用若涉及 Organizations 或帳號層級變更，先由使用者確認。
- group：`AWSFinalProjectDevelopers`。
- permission set：`AWSFinalProjectDeveloper`，使用短期 session，不掛永久 `AdministratorAccess`。
- user：優先沿用唯讀盤點發現的既有 Identity Center user；若需新增，使用者本人確認 Email、顯示名稱、MFA 與邀請流程。
- assignment：只指派到本專題實際使用的 AWS account。
- CLI：建立 SSO profile，不建立 Access Key。

## 當日可建立 role

- `AWSFinalProjectAppRole`：只有確認 Tier 0 採用 EC2 後建立；trust principal 限定 `ec2.amazonaws.com`。
- 基礎 policy：`AmazonSSMManagedInstanceCore`。
- 專案 policy：待 Region、log group、secret／parameter、資料層與 Bedrock model ARN 確定後再建立，所有 resource ARN 必須收斂。
- Instance profile：若採用 EC2，建立並只掛載 `AWSFinalProjectAppRole`。

## 本日不建立

- `AWSFinalProjectLambdaRole`：尚未選定 Lambda。
- `AWSFinalProjectGitHubDeployRole`：尚未啟用 CI/CD，且 repository／branch 邊界未確認。
- `AWSFinalProjectOperatorRole`：屬選配，尚無受控 SSM 操作需求與目標 instance ARN。

## 明確禁止

- 長期 Access Key。
- 應用程式 `AdministratorAccess`、`IAMFullAccess`、`AmazonBedrockFullAccess`、`AmazonS3FullAccess`。
- `iam:PassRole` 的 `Resource: "*"`。
- 未限定的 secret 明文讀取或 public SSH。
