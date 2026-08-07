# AWS Account Plan 變更紀錄

- 日期：2026-08-07（Asia/Taipei）
- 觀察結果：AWS 通知 Free account plan 已自動升級為 Paid plan
- 觸發原因：本日建立 AWS Organization；CloudTrail 已記錄 `CreateOrganization`
- 帳號 ID：不保存

## 成本影響

AWS Organizations 與 IAM Identity Center 本身不額外收服務費，但 AWS Free Tier 現行規則明確指出：Free plan 帳號建立或加入 AWS Organization 時會自動升級為 Paid plan，剩餘 Free Tier credits 立即失效，且無法降回 Free plan。

Paid plan 是 pay-as-you-go，並非固定月費訂閱；只有使用到計費服務或超出適用的免費用量才產生費用。但目前不能再假設有新帳號 Free Tier credits 可抵扣未來 EC2、RDS、Bedrock 或其他服務費用。

## 風險控制

- 保留每月 `US$1.00` Budget 與提醒；Budget 只告警，不是硬性停用上限。
- 建立基礎架構前重新估算所有可能計費服務。
- 避免 NAT Gateway、ALB、multi-Region KMS、閒置 Elastic IP 等非必要費用。
- 到 Billing 的 Credits、Free Tier 與 Bills 頁面確認 credits 與當月實際金額；截圖需遮蔽 account ID、付款與 Email。
- 不為了嘗試恢復 Free plan 而刪除 Organization；官方規則不允許 Paid plan 降級，且刪除會破壞 Identity Center organization instance。
- 不以另一個 Email 重新註冊帳號來規避資格；AWS Free plan 與 Free Tier credits 僅適用於從未擁有 AWS 帳號的新客戶。只有 AWS Support 明確確認資格後才評估新帳號。
- 在 AWS Support Center 建立 `Account and billing` 案件，請求恢復 Free Tier credits 或提供 courtesy credit；Basic Support 可處理帳號與帳務問題。

## 流程根因與矯正

8 月 6 日 handoff 將 IAM Identity Center account access／CLI SSO 列為今日目標，卻沒有記錄 organization instance 對新版 Free plan 的不可逆影響。執行時又只確認 Organizations／Identity Center 服務本身不額外收費，未在 `CreateOrganization` 前驗證 Account plan 與 Credits，造成風險揭露不足。

專題 Skill 與 handoff 已新增硬性關卡：任何 Organizations、Control Tower 或 Identity Center organization instance 寫入前，必須先驗證 Account plan／Credits；Free plan 時停止並取得對「自動 Paid plan、credits 立即失效、不可降級」的特定知情確認。

## 官方依據

- [AWS Free Tier FAQ](https://aws.amazon.com/free/free-tier-faqs/)
- [AWS：Enable IAM Identity Center](https://docs.aws.amazon.com/singlesignon/latest/userguide/enable-identity-center.html)
- [AWS Support Plans](https://docs.aws.amazon.com/awssupport/latest/user/aws-support-plans.html)
