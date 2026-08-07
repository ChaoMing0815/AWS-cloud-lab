# IAM Identity Center 啟用結果

- 日期：2026-08-07（Asia/Taipei）
- 操作身分：Root user
- Instance type：organization instance
- 執行個體範圍：單一區域
- 主要 Region：Tokyo，`ap-northeast-1`
- Identity source：Identity Center directory
- 加密：AWS owned key
- 其他 Region：無
- 結果：啟用成功

## 安全與成本結果

- 未採用 multi-Region replication，未建立 customer-managed KMS primary／replica keys。
- 未建立長期 Access Key。
- 本步驟未建立使用者、group、permission set assignment，也未授予應用程式 `AdministratorAccess`。
- IAM Identity Center 本身不額外收費；本步驟沒有新增 KMS key storage 費用。

## 證據狀態

Console 已顯示 Identity Center Dashboard、Identity Center directory 與主要 Region `ap-northeast-1`，足以確認 AWS 狀態。但原始驗證畫面包含 Organization ID、Issuer URL 與 AWS access portal URLs，依專案證據規範不複製到 repository。

去識別化截圖已保存：保留 Dashboard、Identity source 與主要 Region，並裁掉 Organization ID、Issuer URL、portal URL、Email 與帳號識別資訊。

[IAM Identity Center 啟用完成](../../screenshots/phase0-identity-center-enabled.png)

## 下一步

1. 建立 Identity Center user 與 `AWSFinalProjectDevelopers` group；Email 驗證由使用者本人操作。
2. 設計 `AWSFinalProjectDeveloper` permission set，再取得權限擴張確認。
3. 完成 account assignment、MFA、AWS access portal 與 CLI SSO 正面／負面驗證。
