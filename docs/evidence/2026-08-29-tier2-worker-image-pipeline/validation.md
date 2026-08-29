# Tier 2 Worker image pipeline validation

- 日期：2026-08-29
- Base：`origin/main` exact `7bdd497dbb275fd4bb508b4527ef20c03e5cb89f`
- Branch：`codex/tier2-worker-deployment`
- AWS寫入：本地實作與測試階段無；workflow合併後仍需main dispatch與production人工approval

## 邊界

- 新workflow只允許`workflow_dispatch`與`refs/heads/main`，沿用既有production environment approval及bounded OIDC deploy role。
- 只build／push `linux/arm64` immutable commit image，以build output的exact digest執行Trivy `CRITICAL,HIGH` fail-closed scan。
- 保存commit SHA、workflow run ID、repository URI與image digest的30日artifact，供後續SSM envelope綁定。
- Workflow不含`aws ssm`、`send-command`、既有`CoStoryTier3ContainerRelease`或Web resolution mode，因此不會部署或切換Web。

## TDD與驗證

- Red：2項測試皆只因Worker image workflow不存在而失敗。
- Green targeted：Worker delivery、Worker container與既有container contract合計`23 passed`。
- Backend完整regression：`717 passed, 16 skipped, 1 existing Starlette deprecation warning`。
- `git diff --check`：通過。

## 明確未做

- 尚未dispatch workflow、push新ECR image或產生正式digest manifest。
- 尚未透過SSM部署／啟動任何Worker container。
- 未傳送SQS message、未讀取secret value、未呼叫Bedrock。
- 未修改IAM、CloudFormation 20-resource foundation、Web active digest或Web `sync` mode。
