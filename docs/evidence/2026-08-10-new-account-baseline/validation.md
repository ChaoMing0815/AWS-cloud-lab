# 2026-08-10 新 AWS 帳號安全與成本基線

## 範圍

本紀錄只描述 2026-08-10 重新申請的新 AWS 帳號。2026-08-07 因建立 AWS Organization 導致 Free plan 失效的帳號保留為歷史事故，不得與本帳號狀態混用。

## 已驗證

| 項目 | 結果 | 證據 |
| --- | --- | --- |
| Account plan | Billing Console 顯示 Free plan，未執行升級 | [`phase0-new-account-free-plan.png`](../../screenshots/phase0-new-account-free-plan.png) |
| Budget | 每月 `US$1.00`，目前支出 `US$0.00`，狀態正常 | [`phase0-new-account-budget.png`](../../screenshots/phase0-new-account-budget.png) |
| 當月帳單 | `ming-dev` 可讀取 2026 年 8 月帳單，預估總計 `USD 0.00` | [`phase0-ming-dev-billing-zero.png`](../../screenshots/phase0-ming-dev-billing-zero.png) |
| Root 安全 | Root MFA 已啟用，Root 沒有作用中的 Access Key | [`phase0-new-account-root-mfa.png`](../../screenshots/phase0-new-account-root-mfa.png) |
| 日常人員身分 | IAM user `ming-dev` 已啟用 Console access 與 MFA | [`phase0-new-account-root-and-iam-mfa.png`](../../screenshots/phase0-new-account-root-and-iam-mfa.png) |
| 長期憑證 | `ming-dev` Access Key、API Key 與 CodeCommit SSH key 均為 `0` | [`phase0-ming-dev-zero-keys.png`](../../screenshots/phase0-ming-dev-zero-keys.png) |
| 群組與初始權限 | `AWSFinalProjectDevelopers` 有 1 位成員；連接 `ReadOnlyAccess`、`IAMUserChangePassword` | [`phase0-ming-dev-group-policies.png`](../../screenshots/phase0-ming-dev-group-policies.png) |
| Billing 有效權限 | `ming-dev` 可開啟 2026 年 8 月帳單；現有截圖未證明實際 policy 與附掛位置 | [`phase0-ming-dev-billing-zero.png`](../../screenshots/phase0-ming-dev-billing-zero.png) |

## 尚未完成／不可誤判

- 尚未驗證 Credits 精確餘額與到期日。
- 尚未保存新帳號未建立 AWS Organization 的證據；在此之前不得啟用 IAM Identity Center organization instance、Control Tower 或 Organizations。
- 尚未以 IAM 唯讀盤點確認 `ming-dev` 的 Billing policy 名稱與附掛位置；不得只憑可開啟帳單畫面宣稱群組已連接 `AWSBillingReadOnlyAccess`。
- `ming-dev` 尚未取得 `PowerUserAccess`，目前不能建立或修改大部分 AWS 資源。
- `AWSCourseAccountProtectionDeny` 尚未建立；先前草案中的 `billing:*` 全面拒絕會破壞帳務唯讀，必須改為只拒絕寫入與購買動作，經 IAM policy validation、simulation 與負面測試後才能使用。
- 本日沒有建立 EC2、RDS、VPC、NAT Gateway、Load Balancer 或其他專題 workload。

## 安全邊界與下一個 AWS 起點

1. 平時以 `ming-dev` 登入；Root 在完成帳號層級工作後登出。
2. 不建立人員長期 Access Key，不授予 `AdministratorAccess`。
3. 下次 AWS 工作先以唯讀方式確認 account plan、Credits、Organizations、Region、當月費用與 principal。
4. 由 Root 短暫建立並連接修正版 `AWSCourseAccountProtectionDeny`，先驗證拒絕 `freetier:UpgradeAccountPlan`、Organizations、Control Tower 與購買／承諾動作。
5. 防護政策通過正面與負面驗證後，才另行評估 `PowerUserAccess`；不得把政策存在視為完成。

## 費用與回復

- 已觀察費用：`USD 0.00`。
- IAM user、group、MFA 與 managed policy attachment 本身沒有專題 workload 費用。
- 如需回復人員存取，可由 Root 移除群組政策、停用 Console access 或刪除 `ming-dev`；不得在未確認替代管理入口前刪除唯一可用的人員身分。
