# P0-1 AWS 帳號安全前置驗證摘要

- 驗證日期：2026-08-07（Asia/Taipei）
- 驗證身分：AWS account `Root user`（未在文件保存帳號 ID）
- 帳號型態：AWS Organizations management account；目前畫面顯示單一成員帳號
- 專題預定 Region：Asia Pacific (Tokyo)，`ap-northeast-1`

## 成本與安全盤點

| 項目 | 驗證結果 | 證據 |
| --- | --- | --- |
| AWS Budget | `My Zero-Spend Budget` 運作狀態正常；每月預算 `US$1.00`；目前支出 `US$0.00`；提醒閾值已確認 | [Budget](../../screenshots/phase0-zero-spend-budget-verified.png) |
| Root MFA | 已啟用；IAM 儀表板安全建議為 0 | [Root MFA 與 Access Key](../../screenshots/phase0-root-mfa-and-access-keys.png) |
| Root Access Key | 沒有作用中的 Root Access Key | [Root MFA 與 Access Key](../../screenshots/phase0-root-mfa-and-access-keys.png) |
| AWS Organizations | 已啟用，登入帳號為 management account | [Organizations](../../screenshots/phase0-organizations-management-account.png) |
| CloudTrail Event history | 可查詢最近管理事件；篩選結果包含 Root 的 `ConsoleLogin`，事件來源為 `signin.amazonaws.com` | [ConsoleLogin](../../screenshots/phase0-cloudtrail-console-login.png) |

## 本次 AWS 寫入稽核

CloudTrail 顯示驗證期間曾執行 `CreateOrganization`、`AccountJoinedOrganization`、`CreatePolicy` 與 `CreateServiceLinkedRole` 等事件。這些是啟用 AWS Organizations 及其必要整合時產生的管理事件；目前保留 Organizations，供後續 IAM Identity Center account assignment 使用。AWS Organizations 本身不另收服務費，但建立 Organization 已使 Free account plan 自動升級為 Paid plan，相關 Free Tier credits 依官方規則立即失效；詳見[帳號方案變更紀錄](account-plan-change.md)。本次仍未建立 EC2、RDS、NAT Gateway 等計費基礎架構。

[完整寫入事件畫面（內部稽核）](../../screenshots/phase0-cloudtrail-write-events.png)

CloudShell 的 `CreateSession`、`PutCredentials` 與 `DeleteSession` 是 Console 工作階段相關事件；本次沒有建立長期 Access Key，也沒有在專案保存 AWS credential。

## 判定與後續

P0-1 的帳號安全前置驗證已完成：Budget、Root MFA、Root Access Key、Organizations、Region 與 CloudTrail 均有證據。完整 IAM／IAM Identity Center／既有資源的 CLI 唯讀盤點仍待取得非 Root 的短期 SSO 工作階段後執行；在此之前不建立應用程式 role，也不授予應用程式 `AdministratorAccess`。
