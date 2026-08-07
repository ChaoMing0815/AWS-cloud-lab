# IAM Identity Center 啟用前關卡

- 日期：2026-08-07（Asia/Taipei）
- 操作身分：Root user
- AWS account：AWS Organizations management account（帳號 ID 未保存）
- Region：Asia Pacific (Tokyo)，`ap-northeast-1`
- 啟用前狀態：IAM Identity Center 尚未啟用
- 預定 instance type：organization instance
- 執行個體範圍：單一區域（Tokyo）；不啟用 multi-Region replication

## 預定變更

由使用者將 Console 的預選值由「多區域執行個體」改為「單一區域執行個體」，再按下「啟用」，於 Tokyo 建立 IAM Identity Center organization instance。AWS 會建立並管理 Identity Center／Identity Store 及必要的 service-linked role；後續 permission set assignment 會建立名稱以 `AWSReservedSSO_` 開頭的 AWS 管理角色。

本步驟只啟用 Identity Center，不在同一步建立 user、group、permission set 或 account assignment，也不建立長期 Access Key。

## 安全與成本

- IAM Identity Center 本身不額外收費。
- 使用 AWS owned key，不建立 customer managed KMS key。
- Console 預選的 multi-Region 模式會複寫到 Oregon，且要求建立 customer-managed multi-Region KMS primary／replica keys；每把 KMS key 各有 `US$1/月`（按小時計）的儲存費，另可能產生 request 費用，因此本專題不採用。
- Identity Center organization instance 在 AWS Organizations 中只能選定一個主要 Region；若要更換主要 Region，需刪除既有 instance 後重建，因此本次固定為 Tokyo `ap-northeast-1`。
- Root 只執行首次帳號層級啟用；完成使用者、MFA、permission set、assignment 與 SSO 驗證後，停止以 Root 進行日常操作。

## 驗證與回復

啟用後需驗證 Dashboard 顯示已啟用、instance type、Region、Identity source 與 AWS access portal URL；截圖須遮蔽 Email、帳號 ID 與 portal URL 中不必要的識別資訊。

2026-08-07 寫入前畫面已確認以下最終設定：

- 「單一區域執行個體」已選取。
- 靜態加密為 AWS owned key。
- Permission sets 已啟用。
- 主要 Region 為 Tokyo。
- 其他 Region 為「無」。
- 寫入前「啟用」按鈕尚未執行；使用者其後已明確確認 Root／帳號層級變更並完成啟用。

若在建立任何 assignment 前決定回復，可停用／刪除 IAM Identity Center instance。這會移除 Identity Center 設定，因此執行回復前仍需再次確認。

啟用結果：[IAM Identity Center 啟用結果](enable-result.md)

## 證據

- [啟用前 Console 畫面](../../screenshots/phase0-identity-center-before-enable.png)
- [multi-Region KMS 成本警告（已決定避免）](../../screenshots/phase0-identity-center-multi-region-cost-warning.png)
- [單一區域最終設定審查](../../screenshots/phase0-identity-center-single-region-review.png)
- [AWS：Enable IAM Identity Center](https://docs.aws.amazon.com/singlesignon/latest/userguide/enable-identity-center.html)
- [AWS：IAM Identity Center FAQ](https://aws.amazon.com/iam/identity-center/faqs/)
- [AWS：Using IAM Identity Center across multiple Regions](https://docs.aws.amazon.com/singlesignon/latest/userguide/multi-region-iam-identity-center.html)
- [AWS KMS Pricing](https://aws.amazon.com/kms/pricing/)
- [AWS：Service-linked roles](https://docs.aws.amazon.com/singlesignon/latest/userguide/using-service-linked-roles.html)
