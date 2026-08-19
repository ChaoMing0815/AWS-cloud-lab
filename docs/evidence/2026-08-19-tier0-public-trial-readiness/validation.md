# Tier 0 Batch 9A 與公開試玩 readiness

- 日期：2026-08-19
- 風險：R2 公開 UI／錯誤處理；R3 真實 Bedrock 安全驗證與 AWS release。
- 上游：`docs/product/source-of-truth.md`、Screen States、既有 Guardrail v1 與 bounded Bedrock IAM。
- AWS 操作維持 Console-first；未執行 AWS CLI，未新增 resource、IAM、模型、Guardrail 版本或固定費用服務。
- Batch 9A exact S3 objects 為 `2`，archive checksum `OK`；active release 為 `tier0-20260818-a1160bc`。
- Release gate：application／public Nginx／certificate renewal timer active、staging inactive、HTTPS readiness `200`、首頁 `Cache-Control: no-store`。
- Bounded Bedrock calls 共兩次且已用完：benign 世界生成回 `200` 並填入完整草稿；synthetic prompt-injection request 回 `503`。
- `503` 未附正規化 failure code，無法區分 Guardrail intervention、schema invalid 或其他 provider failure；因此 Prompt Attack smoke 記為未通過／未歸因，不以拒絕表象宣稱安全控制有效。
- 未為釐清而重試，下一次模型呼叫必須另取得 exactly-one bounded approval。
- R2 Red commits：`66ee7b5`、`8c9bde0`；Green：`d2b76ba`。新增近端 loading／安全錯誤、三種常見分隔符、泛用範例、正確 AWS runtime 文案與只含 allowlist failure code 的安全記錄。
- Loading shell Red commit：`816b817`；Green：`f9d4155`。canonical deep route 載入期間不再先顯示 Landing。
- 驗證：targeted Frontend `7 passed` 與 loading shell `8 passed`；Frontend full `83 passed`；targeted Backend `2 passed`；Backend full `308 passed, 8 skipped`；`node --check` 與 `git diff --check` 通過。
- 安全記錄不得包含 prompt、room／player identifier、原始 AWS／provider error、stack trace、ARN、IP、secret 或 credential。
- 殘餘：上述 UI 與安全記錄仍只在本機 branch，須先部署新 release，再以 Browser 驗證；之後才可申請 exactly 1 次 synthetic prompt-injection smoke。
