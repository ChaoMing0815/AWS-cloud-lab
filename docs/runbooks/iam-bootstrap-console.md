# IAM Bootstrap Console Runbook

- 狀態：本機政策已準備；等待 AWS 寫入前最終核准
- 適用帳號：2026-08-13 Batch 0 通過的新 AWS Free plan 帳號
- 執行方式：AWS Console only；不使用 AWS CLI
- 目的：讓 `ming-dev` 一次取得完成專題所需的 service power-user 能力，避免每個 Tier 反覆調整權限

## 變更內容

同一個 bounded IAM batch 只做三件事：

1. 在 Tokyo `ap-northeast-1` 建立 CloudFormation stack `co-story-iam-bootstrap`，上傳 [`infra/cloudformation/iam-bootstrap.json`](../../infra/cloudformation/iam-bootstrap.json)。
2. Stack 建立並附加兩份 customer managed policies 到既有 `AWSFinalProjectDevelopers` group：
   - `AWSCourseAccountProtectionDeny`
   - `AWSFinalProjectIamDelegation`
3. 由 Root 在同一 group 附加 AWS managed `PowerUserAccess`，完成後立即登出 Root。

不建立 IAM user、Access Key、login profile、Organization、Control Tower、Identity Center instance 或任何 workload。

## 權限效果

### `PowerUserAccess`

- 允許建立與管理多數 AWS service resources，供 CloudFormation、VPC、EC2、RDS、CloudWatch、Bedrock、ECR、ECS 等專題工作使用。
- AWS managed policy 本身排除一般 `iam:*`、`organizations:*` 與 `account:*`，只保留少數必要的 service-linked role／唯讀動作。

### `AWSCourseAccountProtectionDeny`

無論其他 Allow policy 為何，明確拒絕：

- 建立／加入 AWS Organizations 的關鍵動作
- Control Tower 與 IAM Identity Center instance bootstrap
- Free account plan upgrade
- Marketplace subscription、Reserved Instances、Reserved DB Instances、Savings Plans 購買
- 建立新 IAM user、Access Key 或 login profile

此 policy 不拒絕 Billing read，因此既有 `AWSBillingReadOnlyAccess` 仍可使用。

### `AWSFinalProjectIamDelegation`

- 只管理 `AWSFinalProject*` role、customer managed policy 與 instance profile。
- 新 role 必須使用 AWS managed `PowerUserAccess` 作 permissions boundary；實際 role policy 仍應只給 workload 所需權限。
- `iam:PassRole` 只允許 `AWSFinalProject*` roles，且只可傳給 EC2、ECS tasks、Lambda 或 CloudFormation。
- GitHub OIDC provider 只允許 `token.actions.githubusercontent.com`。
- 不允許管理 IAM users、groups、Access Keys 或 login profiles。

## Console 執行順序

### 1. Root 建立 IAM bootstrap change set

1. 使用 Root＋MFA 登入。
2. Region 選 `Asia Pacific (Tokyo) ap-northeast-1`。
3. 開啟 `CloudFormation → Stacks → Create stack → With new resources (standard)`。
4. 選 `Upload a template file`，上傳 `infra/cloudformation/iam-bootstrap.json`。
5. Stack name：`co-story-iam-bootstrap`。
6. `DeveloperGroupName` 保持 `AWSFinalProjectDevelopers`。
7. 不新增 notification、service role 或其他 stack option。
8. 勾選 named IAM capability acknowledgement。
9. 先建立 change set，不直接執行；確認只有 2 個 `AWS::IAM::ManagedPolicy`，沒有 replacement／deletion 或其他 resource type。

停止條件：group 不存在、change set 出現 2 個以外的 resources、出現 IAM user／Access Key、stack 不在 Tokyo、或任何未列變更。

### 2. Root 執行 change set 並附加 PowerUserAccess

1. Execute 已核對的 change set。
2. 等待 stack `CREATE_COMPLETE`。
3. 到 `IAM → User groups → AWSFinalProjectDevelopers → Permissions`。
4. 確認兩份 customer managed policies 已附加。
5. 選 `Add permissions → Attach policies`，只附加 AWS managed `PowerUserAccess`。
6. 確認 group 最終 policies：
   - `PowerUserAccess`
   - `ReadOnlyAccess`
   - `AWSBillingReadOnlyAccess`
   - `IAMUserChangePassword`
   - `AWSCourseAccountProtectionDeny`
   - `AWSFinalProjectIamDelegation`
7. 登出 Root。

### 3. `ming-dev` 正面與負面驗證

1. 以 `ming-dev`＋MFA 重新登入，避免沿用舊 session cache。
2. 正面：可開啟 CloudFormation create stack、VPC create 頁與 IAM role list；不需建立 resource。
3. 在 IAM Access Analyzer policy validation 檢查兩份 customer managed policies；保存 findings 或無 finding 畫面。
4. 使用 IAM Policy Simulator 驗證：
   - Allow：`cloudformation:CreateChangeSet`、`ec2:CreateVpc`
   - Explicit deny：`organizations:CreateOrganization`、`freetier:UpgradeAccountPlan`、`iam:CreateAccessKey`
5. 不以實際點擊 Organizations／plan upgrade／購買操作作負面測試。

## 證據

保存到 `docs/screenshots/`：

- `phase0-iam-bootstrap-change-set.png`
- `phase0-iam-bootstrap-stack-complete.png`
- `phase0-ming-dev-power-user-policies.png`
- `phase0-iam-bootstrap-policy-validation.png`
- `phase0-iam-bootstrap-policy-simulation.png`

截圖不得包含 Email、完整 account ID、Access Key、token、OTP 或 password。

## 費用、回復與停止

- IAM managed policies／group attachment 與標準 CloudFormation stack 管理本身沒有專題固定費；本 stack 不建立 workload。
- 回復順序：Root 從 group detach `PowerUserAccess`，再刪除 `co-story-iam-bootstrap` stack；確認兩份 customer managed policies 已移除且 `ming-dev` 回到原 read-only 基線。
- 若 policy validation 出現 security warning、simulation 未如預期、Root session 遺留、或 stack rollback，停止 Batch 1 network 建立並先處理 IAM bootstrap。

## 官方參考

- [PowerUserAccess](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/PowerUserAccess.html)
- [IAM PassRole](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_passrole.html)
- [IAM policy validation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-reference-policy-checks.html)
