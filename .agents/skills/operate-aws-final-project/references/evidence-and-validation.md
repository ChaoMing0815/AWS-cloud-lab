# 證據與驗證規格

## 每階段證據組

- `inventory-summary.md`：時間、profile、principal 類型、account ID 遮罩、Region、結論。
- CLI JSON：原始唯讀輸出；先移除敏感值與不必要識別資訊。
- Console 截圖：只截能證明設定的區域，必要時遮罩 Email、account alias 與識別碼。
- `docs/deployment-log.md`：變更、驗證、費用、回復與證據連結。
- `docs/checkpoints.md`：只有驗證通過才勾選。

## IAM 正面與負面測試

- 正面：必要的 log、metric、SSM registration／command、指定 secret metadata 或指定模型呼叫可用。
- 負面：IAM 修改、其他專案資源、任意 secret、未限定 PassRole、public SSH 與未核准 OIDC subject 不可用。
- 使用 policy validation、simulation 或實際短期 session 驗證；記錄方法與限制。

## 安全處理

- 不執行 `aws configure export-credentials`，不讀取或輸出 credential file。
- 不將 `SecretString`、`SecureString` 解密值、Access Key secret、password、token、cookie、OTP 寫入證據。
- Access Key 盤點只保存 user、狀態、建立時間與最後使用時間；遮蔽 Access Key ID。
- account ID、Email 與 alias 若非驗收必要，使用遮罩或摘要。
