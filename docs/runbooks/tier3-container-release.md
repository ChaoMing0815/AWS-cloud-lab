# Tier 3 container release runbook

## 使用前提

本 runbook 目前只定義 bounded change envelope，不能視為 AWS 已部署。使用者尚未明確核准前，Agent 不執行 AWS CLI、S3 讀取、Bedrock 呼叫或 production deploy。

Production GitHub environment 必須設定 required reviewer；repository variables 只放 `AWS_REGION=ap-northeast-1`、ECR repository name、instance ID 與 deploy role ARN，不放 secrets。AWS 帳號若已有 `token.actions.githubusercontent.com` provider，部署 template 時傳入其 ARN，避免建立第二個 account-wide provider。

## Release gate

1. 確認 exact main commit 已通過 Backend、Frontend、container build 與 HIGH／CRITICAL scan。
2. 確認 ECR previous digest 是目前已驗證 release，且 EC2 `/etc/co-story/container-release.env` 與其一致。
3. 從 main 手動啟動 `Tier 3 container release`，輸入 previous digest。
4. Required reviewer 核對 commit、target／previous digest、instance、Region 與 rollback 後批准 production environment。
5. Workflow 以 OIDC build／push immutable commit tag，掃描 exact digest，再透過 `CoStoryTier3ContainerRelease` 發送 bounded SSM command。
6. 只有 SSM 回傳 `container_release=verified` 且 public Nginx edge 的 `/live`、`/ready` 都為 200 才算完成。
7. 無論成功或失敗，下載 `tier3-delivery-metrics-<run-id>` artifact，依[量測方法](../evidence/2026-08-26-tier3-delivery/deployment-efficiency-method.md)保存原始值；artifact 不取代 AWS health evidence。

## 停止與 rollback

- previous digest 不符 active release：停止，不覆寫主機狀態。
- migration、candidate 或 target health 失敗：停止；target 未啟用或自動恢復 previous digest。
- previous restore health 仍失敗：停止後由使用者以 Console／SSM 執行既有 `CoStoryHealthCheck`，不得改讀 secrets 或直接重試 deploy。
- Rollback 不降版 PostgreSQL schema；所有 Tier 3 migration 必須先證明 previous image 可讀新 schema。

## 成本與清理

新增費用面只有 ECR 儲存與 scan；repository lifecycle 只保留最新十個 image。OIDC、IAM role 與 SSM Document 本身不建立常駐 compute。CloudFormation 對 ECR 設 `Retain`，清理前必須先由使用者確認保留的 rollback digest。
