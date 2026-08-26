# Tier 3 control plane Batch T3A 驗證

- 時間／Region：2026-08-26 11:41（Asia/Taipei）；Tokyo `ap-northeast-1`。
- 核准：使用者明確核准 Batch T3A 建立 Change Set，檢查通過後執行。
- Source：commit `679cd32`；template `infra/cloudformation/tier3-delivery.yaml`；SHA-256 `fe957b88564a5b81540a2437eb7c14731aaf382dfafea80d3dba7f9f5cbc8086`。
- Stack／Change Set：`co-story-tier3-delivery`／`co-story-tier3-delivery0826`。
- Change Set：剛好 5 筆 `Add`；沒有 `Modify`、`Remove` 或 replacement。
- Result：`AppEcrPullPolicy`、`ContainerReleaseDocument`、`GitHubDeployRole`、`GitHubOidcProvider`、`Tier3Repository` 全部 `CREATE_COMPLETE`。
- Screenshot：[stack-resources-create-complete.png](stack-resources-create-complete.png)，SHA-256 `47df661dbe8504a99def9dbaad2de8203d8902ffb361519308072082bd59445d`。
- Sanitization：account-linked managed policy／OIDC physical IDs 已遮蔽；未保存 account ID、Email、ARN、token 或 secret。
- Cost：本批只建立空 ECR 與 IAM／OIDC／SSM control plane；尚未 push image、執行 scan 或新增 compute。
- Production：未執行 SSM release、Docker bootstrap、GitHub workflow、S3 或 Bedrock；active release 未改變。
- Pending verification：deploy role trust／permissions boundary、AppRole pull-only policy、ECR immutable／scan／lifecycle、SSM Document default version與負面 IAM 邊界。
- Rollback：刪除 stack；ECR 設 `Retain`，確認空 repository 後另行刪除；OIDC provider 只有無其他 consumer 時才刪除。
