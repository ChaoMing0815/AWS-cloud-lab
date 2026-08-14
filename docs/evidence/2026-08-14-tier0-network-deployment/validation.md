# Tier 0 IAM Bootstrap 與 Network 部署驗證

- 日期／Region／principal：2026-08-14；Tokyo `ap-northeast-1`；Root 僅執行一次性 IAM bootstrap，完成後改回 Console-only、MFA 的 `ming-dev`。
- AWS CLI：未執行；未修改 `~/.aws`、憑證或 Keychain。
- IAM bootstrap：`co-story-iam-bootstrap` 為 `CREATE_COMPLETE`；`AWSFinalProjectDevelopers` 共有 6 份 policies，包含 `PowerUserAccess`、`AWSCourseAccountProtectionDeny` 與 `AWSFinalProjectIamDelegation`。
- Network create：`co-story-tier0-network` 由 19 筆 `Add` 建立完成；只有 VPC、3 subnets、IGW、route tables、App／DB Security Groups 與規則，不含 EC2、RDS、NAT Gateway、EIP、IAM 或 Bedrock。
- Private boundary：private route table 只有 `10.20.0.0/16 → local`，明確關聯 2 個 DB subnets；DB ingress 只有 PostgreSQL TCP `5432`，來源為 App SG。
- Console discovery：第一次部署後，DB SG 出現 EC2 自動建立的 `All traffic → 0.0.0.0/0` egress；這證明 CloudFormation 的空 `SecurityGroupEgress` list 不足以抑制 service default。
- R3 correction：Red `117bf3b`；Green `a78da19`。依 AWS 官方範例，App／DB SG 加入 `127.0.0.1/32` localhost sink，更新 change set 只有兩個 SG `Modify`、Replacement `False`，stack 最終為 `UPDATE_COMPLETE`。
- Local verification：相關 contracts `8 passed`；完整 Backend `247 passed, 8 skipped`；將 sink CIDR 改為 `0.0.0.0/0` 的 sensitivity 如預期失敗，還原後全綠。
- Final egress：DB 只有 localhost sink；App 只有 localhost sink、HTTPS TCP `443 → 0.0.0.0/0` 與 PostgreSQL TCP `5432 → DB SG`，沒有 allow-all external egress。
- 成本：本批只有 VPC network primitives；無 NAT Gateway、public IPv4、compute 或 database，預期固定費用 `US$0`。後續 EC2／RDS 必須另開成本 envelope。
- Rollback：刪除 `co-story-tier0-network` stack 可回復本批 network；IAM bootstrap 只在整體專題 teardown 時依 runbook 回復。

## 去識別化 Console 證據

- [`IAM bootstrap CREATE_COMPLETE`](../../screenshots/phase0-iam-bootstrap-create-complete.png)
- [`IAM group 最終 policies`](../../screenshots/phase0-iam-group-policies-final.png)
- [`Network 19-resource change set`](../../screenshots/phase0-tier0-network-change-set.png)
- [`Network CREATE_COMPLETE`](../../screenshots/phase0-tier0-network-create-complete.png)
- [`Private DB local-only route`](../../screenshots/phase0-tier0-private-db-route.png)
- [`DB ingress`](../../screenshots/phase0-tier0-db-sg-ingress.png)
- [`預設 egress 問題`](../../screenshots/phase0-tier0-db-sg-default-egress-detected.png)
- [`兩個 SG 的修正 change set`](../../screenshots/phase0-tier0-network-egress-fix-change-set.png)
- [`Network UPDATE_COMPLETE`](../../screenshots/phase0-tier0-network-update-complete.png)
- [`DB final egress`](../../screenshots/phase0-tier0-db-sg-egress-final.png)
- [`App final egress`](../../screenshots/phase0-tier0-app-sg-egress-final.png)
