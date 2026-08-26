# Tier 3 control plane Batch T3A 驗證

## 範圍與結果

- 時間／Region：2026-08-26（Asia/Taipei）；Tokyo `ap-northeast-1`。
- 核准：使用者明確核准 Batch T3A 建立 Change Set，檢查通過後執行。
- Source：commit `679cd32`；template `infra/cloudformation/tier3-delivery.yaml`；SHA-256 `fe957b88564a5b81540a2437eb7c14731aaf382dfafea80d3dba7f9f5cbc8086`。
- Stack／Change Set：`co-story-tier3-delivery`／`co-story-tier3-delivery0826`。
- Change Set：剛好 5 筆 `Add`；沒有 `Modify`、`Remove` 或 replacement。
- Result：`AppEcrPullPolicy`、`ContainerReleaseDocument`、`GitHubDeployRole`、`GitHubOidcProvider`、`Tier3Repository` 全部 `CREATE_COMPLETE`。
- Security verdict：Batch T3A 細部安全驗證通過；OIDC、IAM、ECR 與 SSM 邊界皆與受測 template 一致。

## Console 驗證

- GitHub OIDC role trust：使用者貼出 Console JSON，確認唯一 principal 為 `token.actions.githubusercontent.com`、action 為 `sts:AssumeRoleWithWebIdentity`，並以 `StringEquals` 固定 `aud=sts.amazonaws.com` 與 `sub=repo:ChaoMing0815/AWS-cloud-lab:ref:refs/heads/main`；沒有 wildcard。
- Deploy role boundary：Console 顯示 `AWSFinalProjectGitHubDeployRole` 已設定 AWS managed `PowerUserAccess` permissions boundary。
- Deploy role inline policy：使用者貼出 `CoStoryTier3PublishAndRelease` Console JSON，確認 ECR push 僅限 `co-story-tier3`、`ssm:SendCommand` 僅限 `CoStoryTier3ContainerRelease` 與指定 EC2 instance；沒有 `iam:PassRole`、SSH、S3、Bedrock、Secrets Manager 或刪除權限。
- App role pull policy：使用者確認 `AWSFinalProjectTier3EcrPull` 只附加於 `AWSFinalProjectAppRole`；貼出的 Console JSON只有 ECR token 與 `BatchCheckLayerAvailability`、`BatchGetImage`、`GetDownloadUrlForLayer`，repository 僅限 `co-story-tier3`，沒有 push／delete action。
- ECR：Console 顯示 `co-story-tier3` 為 immutable、AES-256、scan on push、沒有 repository permission policy；使用者確認 images 為 0。Lifecycle rule 為任意 tag、image limit 10、expire。
- OIDC provider：Console 顯示 provider type `OpenID Connect`、provider `token.actions.githubusercontent.com`，且唯一 audience 為 `sts.amazonaws.com`。
- SSM Document：使用者在 Console 確認 `CoStoryTier3ContainerRelease` 為 `Command`、target `/AWS::EC2::Instance`、default/latest version 均為 1、Linux、schema 2.2、timeout 900 秒。參數 pattern 固定東京區域 `co-story-tier3` repository 與兩個 `sha256` digest，執行內容固定使用 `/opt/co-story/current/ops/release/deploy_container.sh` 與 `/etc/co-story/runtime.env`。
- Policy Simulator：`iam:PassRole` denied（permissions boundary）、`ecr:DeleteRepository` denied、`ssm:StartSession` denied；對 `co-story-tier3` 的 `ecr:PutImage` allowed 作為正向控制。
- Sensitivity：相同 `ecr:PutImage` 對 `not-co-story-tier3` 為 implicit deny，證明 repository resource scope 生效。

## 時間與效率基準

- ECR Console 顯示 resource creation time 為 11:31:08。
- Stack 五項資源 `CREATE_COMPLETE` 證據保存於 11:41。
- 人工細部安全驗證截圖區間為 12:01–12:56，約 55 分鐘；這是 control-plane security review 時間，不冒充應用程式部署時間。
- 未來自動部署效率比較應使用 workflow artifact 的 gate／build／scan／approval／SSM／readiness／rollback timestamps，與既有手動部署紀錄採同一起訖定義比較。

## 證據檔與 SHA-256

| 證據 | SHA-256 |
| --- | --- |
| [stack-resources-create-complete.png](stack-resources-create-complete.png) | `47df661dbe8504a99def9dbaad2de8203d8902ffb361519308072082bd59445d` |
| [deploy-role-permissions-boundary.png](deploy-role-permissions-boundary.png) | `a096e55d149837f680a259ab7899f12adf8205459d8d6f50257eb974d102d85a` |
| [ecr-repository-security-settings.png](ecr-repository-security-settings.png) | `caca5f8523729811ba0aec016fb59a13fabeff6a5c893923dffde9d20bd19b8a` |
| [ecr-lifecycle-policy.png](ecr-lifecycle-policy.png) | `6b7cc70147e52f1581a54bf3f9a5a937f35d3212f9b1f0b175c10fa99c4dcedb` |
| [github-oidc-provider.png](github-oidc-provider.png) | `e1f29809afbaf0c7e158c6d9173bb82b78194e512d437c26293bdf20a5b545cd` |
| [deploy-role-policy-simulator.png](deploy-role-policy-simulator.png) | `131e6998919488ef006bbf2c9bfd0e2d1c93f1e2112a1add9f353ef61edc2f14` |
| [deploy-role-cross-repository-deny.png](deploy-role-cross-repository-deny.png) | `ecb042af4b33617ab470f1ad5d2c4bf156c18fd6da19c763e3bf7b1daeed3b54` |

## 安全、成本與回復邊界

- Sanitization：account-linked ARN／URI、Account ID 與 instance ID 已遮蔽；未保存 Email、token、secret 或 credential。文字確認只保留安全不變量，不保存完整 account-linked ARN。
- Cost：本批只建立空 ECR 與 IAM／OIDC／SSM control plane；尚未 push image、執行 scan 或新增 compute。
- Production：未執行 SSM release、Docker bootstrap、GitHub workflow、S3 或 Bedrock；active release 未改變。
- Rollback：刪除 stack；ECR 設 `Retain`，確認空 repository 後另行刪除；OIDC provider 只有無其他 consumer 時才刪除。
