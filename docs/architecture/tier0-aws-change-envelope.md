# Tier 0 AWS 變更封套（分批人工核准）

- 狀態：Draft；本文件不是 AWS 授權，也不代表已有任何 AWS 資源。
- 日期：2026-08-13
- 對象：新 AWS 帳號的單一專題環境。
- 前置事實：2026-08-10 證據顯示 Free plan、每月 `US$1.00` Budget、Root MFA、無 Root Access Key，以及 `ming-dev` 的 Console＋MFA；Credits 精確餘額／到期日、目前 principal、Region 與既有資源仍未以最新唯讀資料確認。

## Batch 0：唯讀盤點（先核准此批）

> 2026-08-13 結果：已由使用者操作 Console 完成並通過；未執行 AWS CLI 或 AWS 寫入。完整去識別化結果與證據見 [`2026-08-13-tier0-batch0-console-inventory`](../evidence/2026-08-13-tier0-batch0-console-inventory/inventory-summary.md)。此結果不授權 Batch 1。

目的：取得建立基礎設施前不可假設的帳號與費用事實；不建立、修改或刪除資源。

| 項目 | 限制 |
| --- | --- |
| Principal／account／Region | 只保存帳號 ID 遮罩、principal 類型與 Region；不輸出 token、Email、Access Key 或 secret。 |
| 帳務 | 確認 account plan、Credits 餘額／到期、Budget、當月成本與 Cost Explorer 可見性。Budget 是告警，非硬性上限。 |
| Organizations | 只確認是否存在；**禁止**建立／加入 Organization、Control Tower 或 Identity Center organization instance。 |
| 資源與 IAM | 盤點現有 VPC、EC2、RDS、NAT Gateway、EIP、CloudWatch、IAM role／policy；不讀取 SecretString 或 SecureString 明文。 |
| 證據 | 依 Skill 保存 sanitized inventory summary、必要 JSON 與 Console 截圖；不記錄 deployment log 的「部署」。 |

停止條件：帳號不是預期新帳號、Free plan／credits 與預期不同、Budget 不存在或告警失效、principal 沒有最小必要權限、存在未知計費資源，或 Region 無法提供所需 RDS／Bedrock，均停止而不進行寫入。

## IAM Bootstrap：一次性課程開發權限（2026-08-14 已完成）

| 項目 | 固定邊界 |
| --- | --- |
| Template | `infra/cloudformation/iam-bootstrap.json`；只建立並附加 `AWSCourseAccountProtectionDeny`、`AWSFinalProjectIamDelegation` 到既有 `AWSFinalProjectDevelopers` group。 |
| Power user | Root 在同一 bounded batch 手動附加 AWS managed `PowerUserAccess` 到該 group；完成後立即登出。 |
| 便利性取捨 | 使用者明確選擇讓 `ming-dev` 一次取得完成 Tier 0–5 所需的大部分 service 權限，不為每個一般操作反覆改權限；此為單人課程帳號決策，不宣稱 production least privilege。 |
| IAM delegation | 只管理 `AWSFinalProject*` role／policy／instance profile；新 role 強制 `PowerUserAccess` permissions boundary；PassRole 只限專題 roles 與 EC2／ECS tasks／Lambda／CloudFormation；GitHub OIDC 只限 `token.actions.githubusercontent.com`。 |
| 明確拒絕 | Organizations／Control Tower／Identity Center instance bootstrap、Free plan upgrade、Marketplace／Reserved／Savings Plans 購買、新 IAM user、Access Key 與 login profile。 |
| 不包含 | 不建立 workload、EC2、RDS、VPC、Bedrock、IAM user、Access Key 或 application role。 |
| 成本／回復 | IAM policies、group attachment 與本 stack 無專題固定費；回復為 detach `PowerUserAccess` 後刪除 `co-story-iam-bootstrap` stack。 |
| 驗證 | Change set 只能有 2 個 `AWS::IAM::ManagedPolicy`；完成後執行 policy validation、Allow simulation 與 explicit-deny simulation。 |

本機 R3 TDD 與完整驗證見 [`2026-08-14-iam-bootstrap-policy`](../evidence/2026-08-14-iam-bootstrap-policy/tdd-validation.md)；Console 步驟見 [`iam-bootstrap-console.md`](../runbooks/iam-bootstrap-console.md)。

## Batch 1：Tier 0 network CloudFormation（僅在 Batch 0 與下列欄位確認後）

> 2026-08-14 結果：使用者已核准並以 Console 完成；stack `co-story-tier0-network` 為 `UPDATE_COMPLETE`。實機發現並以 R3 TDD 修正 EC2 default allow-all egress，最終 App／DB SG、private route 與 19-resource boundary 均通過；全程未使用 AWS CLI。證據見 [`2026-08-14-tier0-network-deployment`](../evidence/2026-08-14-tier0-network-deployment/validation.md)。

| 範圍 | 固定邊界 |
| --- | --- |
| Template | `infra/cloudformation/tier0-network.yaml`；只建 VPC、1 public app subnet、2 private DB subnets、IGW、route tables、App／DB Security Groups。 |
| 不包含 | EC2、RDS、IAM role、instance profile、Secrets Manager、Parameter Store、Bedrock、NAT Gateway、ALB、EIP、SSH key、CI/CD。 |
| 網路 | `10.20.0.0/16`、`10.20.10.0/24`、`10.20.110.0/24`、`10.20.120.0/24`；若與帳號現有 CIDR 重疊，先停止並提出替代 CIDR。 |
| 安全 | Internet 只可到 App `80/443`；絕不開 `22/8000`；DB `5432` 只允許 App SG，無 public IP、無 IGW／NAT default route。 |
| 成本 | VPC、subnet、route table、IGW、Security Group 本身通常沒有固定費；仍須先確認沒有衍生 NAT、EIP、endpoint 或其他未列資源。 |
| 驗證／回復 | CloudFormation validate／change set 後才 create；驗證 subnet route 與 SG 負面規則。失敗則刪除該 stack；成功後只保留 network stack，後續 compute／DB 另開 envelope。 |

## 後續不可併入 network batch 的項目

1. RDS：規格、版本、DB subnet group、encrypted storage、backup／deletion policy、DB master／app credential與 Secrets Manager ARN 都需成本、清理與權限核准。
2. EC2／IAM／SSM／CloudWatch：AMI、instance class、EBS、AppRole policy、instance profile、log group retention 與 SSM boundary 需獨立審查。
3. Bedrock：Region、實際 model 或 inference profile、Guardrail、token ceiling、model access 與最小 ARN policy 需先確認可用性與預期費用。
4. TLS：網域、DNS、certificate／Nginx TLS 檔與 HTTPS Browser 驗證需另決定；沒有真實 HTTPS 不標示為正式上線。

## Batch 2：Tier 0 private PostgreSQL（已部署並驗證）

| 項目 | 固定邊界 |
| --- | --- |
| Template | `infra/cloudformation/tier0-rds.yaml`；只建立 1 個 DB subnet group 與 1 個 RDS DB instance。 |
| Engine／size | RDS API `EngineVersion` 為 PostgreSQL `18.3`（Console 版本描述 `18.3-R2`）、Extended Support disabled、Single-AZ、`db.t4g.micro`、20 GiB gp2、無 storage autoscaling。 |
| Network | 使用 Batch 1 的兩個 private DB subnets 與 DB SG；`PubliclyAccessible=false`；不建立 NAT、public IPv4、proxy 或新 SG。 |
| Credential | RDS-managed master password 存於 Secrets Manager；template、Git 與 Console 截圖都不輸入或保存明文密碼。 |
| Encryption／monitoring | RDS 預設 AWS managed KMS key、Database Insights Standard 7 days；Enhanced Monitoring、DevOps Guru 與 log exports 關閉。 |
| Backup／回復 | backup retention 1 day；失敗刪除 stack；DeletionPolicy 為 Delete，不留持續計費 snapshot。需保留資料時另行核准 snapshot。 |
| 成本上限 | Console compute 牌價 `US$0.029/hour`，730 小時約 `US$21.17/month`；1 個 Secrets Manager secret 約 `US$0.40/month`＋少量 API calls。含 storage／backup buffer，本批 credits burn 上限 `US$25/month`。 |
| 停止日期 | 最晚 2026-09-08 清理或另行核准延長；Free plan／credits 任一異常、change set 超出兩項 resources、public access 或 Multi-AZ 出現時立即停止。 |

本機 R3 TDD 證據見 [`2026-08-14-tier0-rds-iac`](../evidence/2026-08-14-tier0-rds-iac/tdd-validation.md)。本批不包含 EC2、application role、migration、Bedrock 或 production deploy。

> 2026-08-15 結果：修正空白 parameters 與 API `EngineVersion` 後，`co-story-tier0-rds` 為 `CREATE_COMPLETE`；RDS `Available`，Internet access gateway disabled，並使用既有 private DB network boundary。RDS 與 managed secret 已開始消耗 credits。

## Batch 3：Tier 0 EC2＋SSM management plane（已部署並驗證）

| 項目 | 固定邊界 |
| --- | --- |
| Account／principal／Region | 沿用已驗證的新 Free plan account；MFA `ming-dev`；Tokyo `ap-northeast-1`；Console-first、無 AWS CLI。 |
| Template | `infra/cloudformation/tier0-compute.yaml`；只建立 1 個 EC2 instance、1 個 `AWSFinalProjectAppRole` 與 1 個 instance profile。 |
| Compute | Amazon Linux 2023 ARM64、`t4g.micro`、CPU credits `standard`、8 GiB encrypted gp3、detailed monitoring disabled。AMI 由 AWS public SSM parameter 解析。 |
| Network | 使用 Batch 1 public app subnet 與既有 App SG；自動 public IPv4、無 Elastic IP／NAT／ALB／新 SG。App SG 仍只有 public `80/443`，永不開 `22` 或 `8000`。 |
| IAM／SSM | Role trust 只允許 `ec2.amazonaws.com`，使用 `PowerUserAccess` permissions boundary，但實際只掛 `AmazonSSMManagedInstanceCore`；不授予 Secrets Manager、Bedrock、CloudWatch 或 IAM 管理權限。 |
| Host security | IMDSv2 required、hop limit 1、instance metadata tags disabled；不建立 Key Pair、UserData、secret、runtime environment 或 application deployment。 |
| 成本上限 | EC2＋8 GiB gp3＋1 個 public IPv4 的 credits burn 上限 `US$20/month`；public IPv4 官方牌價為 `US$0.005/hour`（約 `US$3.65/month`）。不含既有 RDS 成本。 |
| 失敗／rollback | CloudFormation rollback all resources。刪除 stack 會 terminate instance、刪除 root EBS、釋放自動 public IPv4，並刪除 role／profile；不建立 snapshot。 |
| 停止日期 | 最晚 2026-09-08 清理或另行核准延長；change set 超過 3 項、出現 Key Pair／EIP／新 SG／secret／UserData、非 `t4g.micro` 或 role 多出 policy 時立即停止。 |
| 正面驗證 | Stack `CREATE_COMPLETE`；EC2 running／2-of-2 checks；SSM managed node online；Console Session Manager 可連線。 |
| 負面驗證 | EC2 沒有 Key Pair／SSH ingress；IMDSv2 required；AppRole 只有 SSM core；無 EC2、EBS、public IPv4、IAM 殘留於 rollback。 |

本機 R3 TDD 證據見 [`2026-08-15-tier0-compute-iac`](../evidence/2026-08-15-tier0-compute-iac/tdd-validation.md)。本批不包含 application code、DB credential、migration、TLS、Bedrock、CloudWatch logs 或 CI/CD。

> 2026-08-15 結果：`co-story-tier0-compute` 為 `CREATE_COMPLETE`；EC2 running 且 health checks passed，SSM managed node Online。Console Session Manager 以 `ssm-user` 登入，實機確認 ARM64 `aarch64` 與 SSM Agent active；無 Key Pair、SSH 或 AWS CLI。

## Batch 4：application DB credential、migration 與 internal runtime（internal staging 完成）

| 項目 | 固定邊界 |
| --- | --- |
| Account／principal／Region | 沿用 MFA `ming-dev` 與 Tokyo `ap-northeast-1`；Console-first、無 SSH。只有使用者逐批核准後，才在 EC2 的 SSM Session 內執行 exact-prefix S3 download 與安裝指令；未修改本機 AWS credentials。 |
| Secrets template | `infra/cloudformation/tier0-runtime-secrets.yaml`；只建立 1 個 generated application DB secret 與 2 份 exact-resource managed policies。不得保存 password 明文或固定 secret physical name。 |
| Permanent access | 既有 `AWSFinalProjectAppRole` 只可 `DescribeSecret`／`GetSecretValue` 該 generated application secret。 |
| Temporary bootstrap | `EnableMigrationBootstrapAccess=true` 時只可讀 Batch 2 的 RDS master secret ARN；建立／更新 `co_story_app` 並 migration 完成後，必須以 stack update 改為 `false`，使 temporary policy 被刪除。 |
| DB boundary | `co_story_app` 固定為 LOGIN，但必須是 `NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS`；只連 `co_story` 並在 `public` schema 建立／使用專題 migration objects。TLS 固定 `sslmode=verify-full`＋RDS CA。 |
| Host secret | DSN 只寫入 `/etc/co-story/database.env`，owner `root:co-story`、mode `0640`、原子 replace；不得出現在 template、Run Command parameters、shell history、Git 或截圖。 |
| Artifact path | `infra/cloudformation/tier0-deployment-artifacts.yaml` 已部署：generated-name bucket、四項 Block Public Access、SSE-S3、BucketOwnerEnforced、TLS-only、`releases/` 7 日到期，AppRole 只有 exact prefix list／read。 |
| 成本 | Change Set 本身無費用。Execute 後新增 1 個 Secrets Manager secret，可能約 `US$0.40/month` 加少量 request；短期 S3 只有少量 storage／request usage。無 NAT／ALB／EIP／新 compute／新 DB。 |
| Rollback | migration 前可刪 secrets stack；migration 後先將 bootstrap access 改 `false`。Artifact bucket 清空 objects 後刪 stack。DB schema 採 forward-only，不做自動 downgrade。 |
| 停止條件 | Change Set 超過 3 項或含非 Secret／IAM policy、任何 `Resource: *`、public bucket、secret value、master access 無法撤除、DB user 取得管理權限或 TLS 非 `verify-full` 時停止。 |

> 2026-08-16 結果：artifacts 與 runtime-secrets stacks 已建立；release `tier0-20260816-b028569` 已在 EC2 internal staging 啟用，FastAPI／Nginx services active，loopback readiness HTTP `200`。restricted DB role 與 migration 完成後，CloudFormation update 只移除 temporary master-secret policy，並為 `UPDATE_COMPLETE`。Backend regression `290 passed, 8 skipped`。公開 Web／TLS 與真實 Bedrock invocation 不在本批成果內；去識別化摘要見 [`2026-08-16-tier0-internal-staging`](../evidence/2026-08-16-tier0-internal-staging/validation.md)。

## Batch 5：Bedrock Guardrail＋bounded runtime IAM（已部署，尚未真實 invocation）

| 項目 | 固定邊界 |
| --- | --- |
| Region／model | Tokyo `ap-northeast-1`；固定 model `amazon.nova-lite-v1:0`，Serverless／Standard；不得使用 Marketplace、Batch 或 Global inference。 |
| Guardrail | `co-story-tier0-safety`；Standard tier、APAC cross-Region profile `apac.guardrail.v1:0`、default KMS。使用者已明確同意資料僅在 APAC geographic boundary 內跨區域處理。 |
| Content | Hate High、Insults Medium、Sexual High、Violence Low、Misconduct Low，prompt／response Block；Prompt Attack High。只處理 Text。 |
| Privacy | EMAIL／PHONE input／output 均 Mask；無 regex。Denied topics、Profanity、custom words、Grounding、Relevance 全部停用。 |
| Price baseline | Nova Lite Standard：input `US$0.072／1M tokens`、output `US$0.288／1M tokens`；Guardrail 另按啟用政策的 text units 計費。 |
| 固定版本／IAM | Guardrail version `1`；既有 AppRole 只允許 exact Nova Lite `InvokeModel`，以 versioned Guardrail ARN condition fail closed，並只允許來源 Guardrail與 Tokyo profile 的六個 APAC destination `ApplyGuardrail` ARN；不授予串流、其他 model 或 Full Access。 |
| 尚未執行 | 不 Test、不 Invoke model、不啟用 invocation logging；真實 allow／block／PII mask 與故事生成留待另批極小 token 預算驗證。 |
| 停止條件 | 出現 Global profile、Marketplace subscription、Provisioned Throughput、未限定 model／Guardrail 的 `Resource: *`、明文 prompt logging 或單次測試無 token ceiling 時停止。 |

> 2026-08-15 結果：Guardrail resource 建立完成且 status `Ready`；未進行任何 Test／model invocation，未發布或驗證固定 version，EC2 AppRole 仍無 Bedrock 權限。證據摘要見 [`2026-08-15-tier0-bedrock-guardrail`](../evidence/2026-08-15-tier0-bedrock-guardrail/validation.md)。

> 2026-08-17 結果：使用者核准 Batch 5A 後發布固定 version `1`；`co-story-tier0-compute` change set 只有 `AppRole Modify / Replacement=False`，執行後為 `UPDATE_COMPLETE`。Policy Simulator 正面 exact v1 為 `Allowed`、代表性 v2 為 `Denied`；IAM Console 未顯示 Access Analyzer validation pane，因此該項誠實記為未執行。未 Test、未 Invoke model、未啟用 logging，無新增固定費資源。R3 證據見 [`2026-08-17-tier0-bedrock-runtime-iam`](../evidence/2026-08-17-tier0-bedrock-runtime-iam/tdd-validation.md)。

## 必填核准欄位

- Batch：`0 唯讀盤點` 或 `1 network CloudFormation`（不得以一般「開始 AWS」同意代替）。
- 帳號：新帳號，帳號 ID 僅在受控證據中遮罩保存。
- Region：待 Batch 0 盤點確認；建議依 Bedrock／RDS 可用性選單一 Region。
- 最大成本與停止日期：待使用者在 Pricing Calculator estimate 後填入。
- 執行者與 principal：待 Batch 0 確認，僅用 MFA／短期憑證；禁止長期 Access Key。
- 清理責任：使用者確認；network batch 失敗或不再使用時刪除該 stack，且確認無殘留 NAT／EIP／endpoint。
