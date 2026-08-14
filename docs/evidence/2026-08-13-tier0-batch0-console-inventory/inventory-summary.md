# Tier 0 Batch 0 Console 唯讀盤點摘要

- 日期：2026-08-13
- 盤點方式：使用者操作 AWS Management Console；Agent 引導與整理證據
- 範圍：Tier 0 Batch 0 唯讀盤點
- AWS CLI：未執行
- AWS 寫入：未執行

## 盤點進度

| 步驟 | 時間（Asia/Taipei） | 項目 | 去識別化結果 | 判定 |
| --- | --- | --- | --- | --- |
| Batch 0.1 | 2026-08-13 20:49 | Console 工作階段邊界 | 使用者私下確認為候選部署帳號；principal 類型為 IAM user；本次登入使用 MFA；Account 頁面顯示 `Global` | 通過；`Global` 不是部署 Region 證據，Region 仍待區域性服務頁面確認 |
| Batch 0.2 | 2026-08-13 20:54–20:56 | Account plan 與 Credits | Billing and Cost Management 顯示 Free plan；截至畫面時間尚餘 `181 days`，結束日為 `2027-02-09`；2 筆 credits 均為 `Active`；總額與剩餘額皆為 `US$120.00`，已使用 `US$0.00`；兩筆 credits 到期日皆為 `2027-08-09` | 通過；Free plan 有效期與 credits 均涵蓋 2026-09-07 專題期限並留有清理時間；仍須持續監控使用量，且不得建立／加入 AWS Organizations 或設定 Control Tower |
| Batch 0.3 | 2026-08-13 20:59 | Budget 基本狀態 | `My Zero-Spend Budget` 為 `Healthy` 的 monthly cost budget；金額 `US$1.00`；本月實際支出 `US$0.00`（`0.00%`）；forecast 金額顯示 `-`；開始日 `2026-08-01`，無結束日；Alerts thresholds 顯示 `OK` | 基本狀態通過；forecast 應記為尚無資料；告警門檻與通知目的地仍待唯讀明細確認 |
| Batch 0.3a | 2026-08-13 21:03–21:10 | Budget 告警 | Alerts 頁顯示 `Alerts (1)`；使用者在未儲存的編輯畫面確認 Trigger `Actual`、absolute threshold `US$0.01`、Email recipient 已實際填入、SNS 空白且無 actions；未保存 Email 值 | 通過；告警門檻與 Email subscriber 符合 Zero-Spend 目的，SNS 與 actions 非必要。現行 Console 畫面沒有 alert 選取框且 `View details` 不可用；使用者已退出編輯且未儲存，無 AWS 寫入 |
| Batch 0.4 | 2026-08-13 21:15 | Cost Explorer 可見性 | IAM user 可直接開啟 Cost Explorer，無啟用提示；`2026-02-01` 至 `2026-07-31`、monthly、group by Service 顯示總成本 `US$0.00`、平均月成本 `US$0.00`、service count `0` | 可見性通過；該日期不含 2026 年 8 月，只能作為歷史零成本證據，本月至今仍待查 |
| Batch 0.4a | 2026-08-13 21:20 | 2026 年 8 月本月至今成本摘要 | `2026-08-01` 至 `2026-08-13`、monthly、group by Service、無 filters；畫面顯示 total cost `-US$0.00`、average monthly cost `-US$0.00`、service count `7` | 成本摘要通過；總額四捨五入為零，但 7 個服務代表存在零成本／折抵後的 billing records，尚不能等同「沒有服務活動」；須查看 service breakdown 排除未知項目 |
| Batch 0.4b | 2026-08-13 21:22 | 2026 年 8 月服務成本明細 | 7 個服務為 S3、Glue、Key Management Service、Secrets Manager、SNS、SQS、Data Transfer；各列均為 `US$0.00` 或 `-US$0.00`，total costs `-US$0.00` | 通過；本月至今無可見淨成本，且未出現 EC2、RDS、NAT Gateway、Elastic Load Balancing、CloudWatch 或 Bedrock 費用。billing records 不等於目前仍有資源，資源存在性仍須逐服務盤點 |
| Batch 0.5 | 2026-08-13 21:24 | AWS Organizations | Organizations 起始頁只顯示 `Create an organization`，沒有 Organization ID、Root／OU 或 member account 結構 | 通過；目前未建立或加入 AWS Organization。禁止點擊建立／加入；服務本身不收費不代表 Free plan 無風險，建立／加入仍會觸發 Paid plan／credits 硬性關卡 |
| Batch 0.6 | 2026-08-13 21:27 | 候選盤點 Region | 區域性 EC2 頁面顯示 `Asia Pacific (Tokyo)`，對應 `ap-northeast-1`；未建立資源 | 設定通過；畫面中的 IAM user 名稱不是 credential，且已是專案既有公開識別名稱，因此可納入 repo。Tokyo 仍須完成 RDS／Bedrock 可用性檢查後才成為最終 Region |
| Batch 0.7 | 2026-08-13 21:31 | Tokyo RDS | RDS Databases 頁在 `Asia Pacific (Tokyo)` 顯示 `Databases (0)`、`No resources` | 通過；Tokyo 可開啟 RDS，目前沒有 DB instance 或 cluster，未執行任何建立／還原／購買操作 |
| Batch 0.8 | 2026-08-13 21:36 | Tokyo Amazon Bedrock Model catalog | 使用者確認 Region 為 Tokyo；Model catalog 顯示 `215` 個項目，其中 `63` 個 Serverless，Text filter 顯示 `61`；目前 IAM user 不具模型執行權限 | Catalog 可見性通過；不代表已具 `bedrock:InvokeModel` 或選定最終模型。Anthropic 顯示首次使用需提交 use case details，屬外部資料提交，未經特定核准不得執行；本步未呼叫模型、未訂閱 Marketplace、未建立 API key／Guardrail |
| Batch 0.9 | 2026-08-13 21:39 | Tokyo VPC dashboard | VPC `1`、subnet `3`、route table `1`、internet gateway `1`、network ACL `1`、security group `1`、DHCP option set `1`；NAT gateway、Elastic IP、endpoint、endpoint service、VPC peering、egress-only IGW、customer／virtual private gateway、Site-to-Site VPN、EC2 Instance Connect Endpoint 與 running instance 均為 `0` | 基線部分通過；目前沒有 NAT Gateway、EIP、endpoint 或 running EC2 的明顯計費面。既有項目符合 default VPC 常見組合，但仍須由 VPC 清單確認 `Is default` 與 CIDR，排除 Batch 1 的 `10.20.0.0/16` 重疊 |
| Batch 0.9a | 2026-08-13 | Default VPC CIDR | 使用者在 VPC 清單確認唯一 VPC 的 `Is default = Yes`，IPv4 CIDR 為 `172.31.0.0/16` | 通過；與 Batch 1 預定 `10.20.0.0/16` 不重疊，可沿用原定專題 CIDR。未修改 default VPC |
| Batch 0.10 | 2026-08-13 | IAM 安全基線續驗 | 沿用 2026-08-10 Console 證據：Root MFA、Root Access Key `0`、`ming-dev` MFA、`ming-dev` Access／API／SSH keys `0`，群組 policies 為 `ReadOnlyAccess`、`AWSBillingReadOnlyAccess`、`IAMUserChangePassword`；使用者確認 2026-08-10 後未新增 Access Key、IAM user／role／policy，未變更群組 policies，Root MFA 仍啟用 | 通過；目前沒有長期 Access Key、未知 IAM principal／policy 變更或 Root MFA 退化的跡象。此確認不授權後續 IAM 寫入或權限擴張 |
| Batch 0.11 | 2026-08-13 21:48 | CloudTrail 寫入事件 | Event history 以 `Read-only = false` 篩選，共 5 筆，全部發生於帳號建立日 2026-08-10：2 筆 EC2 default VPC 自動建立事件，以及 Resource Explorer onboarding 的 `CreateIndex`、`CreateView`、`AssociateDefaultView` | 通過；事件與新帳號 default VPC／Resource Explorer 自動 setup 一致，未見 Organizations、EC2 instance、RDS、NAT Gateway、EIP、VPC endpoint 或未知 IAM 寫入。Resource Explorer onboarding 不是專題 workload；Cost Explorer 已證明本月至今淨成本為零 |

## 使用者帳號現況聲明

- 2026-08-13：使用者確認此帳號除建立 IAM user 外，不曾主動使用其他 AWS 功能；目前 VPC dashboard 所見項目均為 AWS default resources。
- 本聲明搭配 Cost Explorer 零成本、RDS `0`、running EC2 `0`、NAT Gateway `0`、Elastic IP `0` 與 endpoint `0` 的 Console 證據，足以停止逐服務空頁盤點。
- Batch 1 前仍須取得唯一 default VPC 的精確 CIDR，因為這是 `10.20.0.0/16` 是否可安全使用的直接衝突條件；其餘盤點收斂為 IAM 安全摘要與 CloudTrail 最近事件兩個關卡。

## Console 證據

- [Free plan 狀態](../../screenshots/phase0-tier0-batch0-account-plan.png)
- [Free plan 結束日與剩餘天數](../../screenshots/phase0-tier0-batch0-free-plan-expiration.png)
- [Credits 摘要](../../screenshots/phase0-tier0-batch0-credits-summary.png)
- [Credits 明細與到期日](../../screenshots/phase0-tier0-batch0-credits-detail.png)
- [Budget 基本狀態](../../screenshots/phase0-tier0-batch0-budget-status.png)
- [Budget 告警清單](../../screenshots/phase0-tier0-batch0-budget-alert-list.png)
- [Cost Explorer 可見性與歷史零成本](../../screenshots/phase0-tier0-batch0-cost-explorer-visibility.png)
- [2026 年 8 月本月至今成本摘要](../../screenshots/phase0-tier0-batch0-current-month-cost.png)
- [2026 年 8 月服務成本明細](../../screenshots/phase0-tier0-batch0-current-month-service-breakdown.png)
- [未建立 AWS Organization](../../screenshots/phase0-tier0-batch0-no-organization.png)
- [Tokyo 候選盤點 Region](../../screenshots/phase0-tier0-batch0-region-tokyo.png)
- [Tokyo RDS 無資料庫資源](../../screenshots/phase0-tier0-batch0-rds-tokyo-empty.png)
- [Tokyo Amazon Bedrock Model catalog](../../screenshots/phase0-tier0-batch0-bedrock-tokyo-catalog.png)
- [Tokyo VPC dashboard](../../screenshots/phase0-tier0-batch0-vpc-dashboard-tokyo.png)
- [Tokyo VPC dashboard 零資源項目](../../screenshots/phase0-tier0-batch0-vpc-dashboard-tokyo-zero-resources.png)
- [2026-08-10 IAM／帳號安全基線](../2026-08-10-new-account-baseline/validation.md)
- [CloudTrail 非唯讀事件](../../screenshots/phase0-tier0-batch0-cloudtrail-write-events.png)

## 尚待盤點

- Tokyo 最終 Bedrock model／inference profile、模型執行權限與 Guardrail（後續獨立 change envelope）
- VPC、EC2、RDS、NAT Gateway、EIP 與 CloudWatch 資源

## Batch 0 結論

- 狀態：**通過**；2026-08-13 Console 唯讀盤點完成。
- Account plan／成本：Free plan 至 `2027-02-09`；credits `US$120.00`、最早於 `2027-08-09` 到期；本月至今淨成本 `US$0.00`；每月 `US$1.00` Budget 與 `US$0.01` Actual Email alert 正常。
- 帳號安全：未建立／加入 AWS Organization；Root／`ming-dev` MFA 與零長期 Access Key 基線維持；沒有新增 IAM principal／policy。
- Region／資源：候選 Region 為 Tokyo `ap-northeast-1`；RDS `0`、running EC2 `0`、NAT Gateway `0`、EIP `0`、endpoint `0`；唯一 default VPC 為 `172.31.0.0/16`，不與 `10.20.0.0/16` 重疊。
- Bedrock：Tokyo catalog 可見，但最終 model／inference profile、`bedrock:InvokeModel`、Guardrail 與 Anthropic use case 外部提交仍未核准或驗證，不得標示為正式整合完成。
- AWS 寫入：本批未執行任何使用者發起的 AWS 寫入，也未執行 AWS CLI；CloudTrail 所見非唯讀事件皆為 2026-08-10 新帳號 onboarding。
- 下一步：另行提出 Batch 1 network CloudFormation 的精確人工核准；Batch 0 通過本身不授權任何 AWS 寫入。

## 安全與證據限制

- 未保存完整 AWS account ID、Email、account alias、密碼、OTP、token 或 credential。
- 本步未要求保存 Console 截圖；帳號符合性由使用者在 Console 私下比對。
- 在 Batch 0 完成且停止條件全部排除前，不進行任何 AWS 寫入。
