# IAM Identity Center 與角色邊界

## 人員存取

- 建議 group：`AWSFinalProjectDevelopers`。
- 建議 permission set：`AWSFinalProjectDeveloper`。
- 使用 MFA 與 AWS CLI SSO profile；不建立長期 Access Key。
- Permission set 只允許專題開發所需服務與資源。避免永久 `AdministratorAccess`；bootstrap 若確實需要較寬權限，記錄理由、核准人、到期日與收斂步驟。
- 完成 account assignment 後，同時驗證允許的專題操作與拒絕的 IAM／帳務高風險操作。

## `AWSFinalProjectAppRole`

- Trust：只允許實際採用的 compute service，例如 `ec2.amazonaws.com`；不要同時信任未使用的服務。
- 基礎能力：若使用 EC2，掛載 `AmazonSSMManagedInstanceCore`。
- 自訂 policy：限定專題 log group、metric namespace、secret／parameter、資料儲存與實際採用的 Bedrock model ARN。
- 禁止：IAM 管理、組織／帳務修改、未限定 Secrets Manager 讀取、服務級 Full Access、`AdministratorAccess`。

## `AWSFinalProjectLambdaRole`

- 只在已選定 Lambda 時建立。
- Trust：`lambda.amazonaws.com`。
- 使用 Lambda 基礎 logging 能力，再以限定 ARN 的自訂 policy 增加資料與模型存取。

## `AWSFinalProjectGitHubDeployRole`

- 只在 CI/CD 啟用時建立。
- 使用 GitHub OIDC，不建立 GitHub 長期 AWS key。
- Trust 限定 `token.actions.githubusercontent.com`、audience `sts.amazonaws.com`、精確 repository 與 branch／environment subject。
- `iam:PassRole` 只能傳遞明確 deployment role，且搭配 `iam:PassedToService` 條件。

## `AWSFinalProjectOperatorRole`

- 選配。限定 CloudWatch 讀取、EC2 描述與受控 SSM 文件／instance 操作。
- 不允許 IAM 修改、任意 `ssm:SendCommand`、讀取 secret 明文或繞過 application role。

## 驗證

1. 使用 IAM Access Analyzer `validate-policy` 檢查每份 policy。
2. 檢查 trust policy 與 permissions policy 是不同文件、各自 principal 正確。
3. 正面測試必要操作可以執行。
4. 負面測試 IAM 變更、未核准 resource、未核准 Region／branch 與 secret 明文存取遭拒。
5. 保存去識別化輸出；不得保存 session token、OTP 或 secret value。
