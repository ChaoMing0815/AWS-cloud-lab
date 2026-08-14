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

## IAM Bootstrap：一次性課程開發權限（使用者已同意方向；等待 Console change set）

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

## 必填核准欄位

- Batch：`0 唯讀盤點` 或 `1 network CloudFormation`（不得以一般「開始 AWS」同意代替）。
- 帳號：新帳號，帳號 ID 僅在受控證據中遮罩保存。
- Region：待 Batch 0 盤點確認；建議依 Bedrock／RDS 可用性選單一 Region。
- 最大成本與停止日期：待使用者在 Pricing Calculator estimate 後填入。
- 執行者與 principal：待 Batch 0 確認，僅用 MFA／短期憑證；禁止長期 Access Key。
- 清理責任：使用者確認；network batch 失敗或不再使用時刪除該 stack，且確認無殘留 NAT／EIP／endpoint。
