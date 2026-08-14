# Tier 0 private RDS IaC 驗證摘要

- Scope／risk：R3；private PostgreSQL、master credential、RDS 固定成本與 teardown data-loss boundary。
- Console inventory：Tokyo Free tier 提供 PostgreSQL、Single-AZ、`db.t4g.micro`、20 GiB gp2；Console 牌價為 `US$0.029/hour`。專題 VPC 因尚無 DB subnet group 而未出現在手動建立 wizard，因此停止手動建立。
- Red：`7d6cebd`；5 項 tests 因 `infra/cloudformation/tier0-rds.yaml` 尚未存在而預期失敗。
- Green：`58fb058`；template 只含 `AWS::RDS::DBSubnetGroup` 與 `AWS::RDS::DBInstance`。
- Engine／size：PostgreSQL `18.3-R2`、Extended Support disabled、Single-AZ、`db.t4g.micro`、20 GiB gp2、無 storage autoscaling。
- Network：兩個 private DB subnet parameters、既有 DB SG parameter、`PubliclyAccessible=false`、port `5432`；不建立 public IPv4、NAT、proxy 或新 SG。
- Credential／encryption：`ManageMasterUserPassword=true`，不接受 hardcoded password；RDS 產生並管理 Secrets Manager secret；storage encryption 使用 RDS 預設 AWS managed key。
- Operations：backup retention 1 day、刪除 stack 時刪除 automated backups、deletion protection false、auto minor upgrade、Database Insights Standard 7 days、Enhanced Monitoring off。
- Local verification：RDS＋network＋IAM contracts `13 passed`；完整 Backend `252 passed, 8 skipped`。
- Sensitivity：將 `PubliclyAccessible` 改為 true，以及將 managed master password 改為 false，對應 tests 均如預期失敗；已還原並全綠。
- AWS：尚未建立 change set 或 RDS resources；全程未使用 AWS CLI。
- Rollback：建立失敗或使用者要求清理時刪除 RDS stack；template 的 `DeletionPolicy`／`UpdateReplacePolicy` 為 `Delete`，不留下持續計費 snapshot。正式資料若需保留，teardown 前另行核准 snapshot。
