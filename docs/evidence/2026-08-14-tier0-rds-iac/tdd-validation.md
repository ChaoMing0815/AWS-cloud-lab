# Tier 0 private RDS IaC 驗證摘要

- Scope／risk：R3；private PostgreSQL、master credential、RDS 固定成本與 teardown data-loss boundary。
- Console inventory：Tokyo Free tier 提供 PostgreSQL、Single-AZ、`db.t4g.micro`、20 GiB gp2；Console 牌價為 `US$0.029/hour`。專題 VPC 因尚無 DB subnet group 而未出現在手動建立 wizard，因此停止手動建立。
- Red：`7d6cebd`；5 項 tests 因 `infra/cloudformation/tier0-rds.yaml` 尚未存在而預期失敗。
- Green：`58fb058`；template 只含 `AWS::RDS::DBSubnetGroup` 與 `AWS::RDS::DBInstance`。
- Engine／size：RDS API `EngineVersion` 為 PostgreSQL `18.3`（Console 版本描述 `18.3-R2`）、Extended Support disabled、Single-AZ、`db.t4g.micro`、20 GiB gp2、無 storage autoscaling。
- Network：兩個 private DB subnet parameters、既有 DB SG parameter、`PubliclyAccessible=false`、port `5432`；不建立 public IPv4、NAT、proxy 或新 SG。
- Credential／encryption：`ManageMasterUserPassword=true`，不接受 hardcoded password；RDS 產生並管理 Secrets Manager secret；storage encryption 使用 RDS 預設 AWS managed key。
- Operations：backup retention 1 day、刪除 stack 時刪除 automated backups、deletion protection false、auto minor upgrade、Database Insights Standard 7 days、Enhanced Monitoring off。
- Local verification：RDS＋network＋IAM contracts `13 passed`；完整 Backend `252 passed, 8 skipped`。
- 2026-08-15 AWS Red：第一次執行因三個 network parameters 留空而在驗證階段 rollback；第二次填入正確 IDs 後，RDS 回報找不到 `EngineVersion 18.3-r2`。兩次均 rollback，未留下 RDS instance。
- 2026-08-15 修正：官方欄位 `EngineVersion` 與 Console 的版本描述不同；test-first 將 IaC contract 改為 `18.3` 並禁止 `-R` suffix。Red 為舊 template `18.3-R2` 造成 targeted test 失敗；Green 為 RDS＋network＋IAM contracts `13 passed`。
- Sensitivity：將 `PubliclyAccessible` 改為 true，以及將 managed master password 改為 false，對應 tests 均如預期失敗；已還原並全綠。
- AWS Green：`tier0-rds-20260815-v2` 只有 `Database` 與 `DbSubnetGroup` 兩筆 `Add`；執行後 `co-story-tier0-rds` 與 Database 均為 `CREATE_COMPLETE`，RDS 為 `Available`。Console 驗證 PostgreSQL `18.3`、Extended Support disabled、Single-AZ、`db.t4g.micro`、20 GiB gp2、encrypted、storage autoscaling disabled、Database Insights Standard 7 days、Enhanced Monitoring disabled與 RDS-managed master secret；Internet access gateway disabled，DB SG inbound 為 App SG、outbound 為 `127.0.0.1/32` sink。全程未使用 AWS CLI。
- Rollback：建立失敗或使用者要求清理時刪除 RDS stack；template 的 `DeletionPolicy`／`UpdateReplacePolicy` 為 `Delete`，不留下持續計費 snapshot。正式資料若需保留，teardown 前另行核准 snapshot。

Console 證據：[`RDS change set only`](../../screenshots/phase0-tier0-rds-change-set.png)、[`空白參數 rollback`](../../screenshots/phase0-tier0-rds-parameter-validation-failure.png)、[`EngineVersion rollback`](../../screenshots/phase0-tier0-rds-engine-version-failure.png)、[`stack CREATE_COMPLETE`](../../screenshots/phase0-tier0-rds-stack-create-complete.png)、[`RDS Available`](../../screenshots/phase0-tier0-rds-available-summary.png)、[`configuration`](../../screenshots/phase0-tier0-rds-configuration.png)、[`internet access disabled`](../../screenshots/phase0-tier0-rds-internet-access-disabled.png)、[`DB SG rules`](../../screenshots/phase0-tier0-rds-security-group-rules.png)。
