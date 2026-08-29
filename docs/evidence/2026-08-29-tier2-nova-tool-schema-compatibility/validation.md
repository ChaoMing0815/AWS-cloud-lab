# Tier 2 Nova Lite tool schema 相容性驗證

- 範圍／風險：修正 production Story Worker 對 `amazon.nova-lite-v1:0` 的 Bedrock Converse tool request；R3。Web runtime 維持 `sync`，不變更 IAM、Guardrail、Region、model ID、SQS、CloudFormation 或資料 schema。
- AWS 失敗證據：exactly-one job 完成 typed JSONB producer、publisher、SQS dispatch、Worker claim 與 completion，但 room 結果為 `INVALID_MODEL`；兩台 Worker 均為 `ap-northeast-1`、`amazon.nova-lite-v1:0`、Guardrail version `1`、async，服務與 container healthy。測試 DB marker 已清除，主佇列與 DLQ 的 available／in-flight 四項皆為 `0`。
- 上游依據：AWS Nova Lite model card確認 Tokyo、Converse、Guardrails與client-side tool calling受支援，但 Structured outputs不受支援；AWS Nova v1 tool schema文件與troubleshooting列出 tool schema subset；Bedrock structured-output文件列出不支援的字串長度 constraints。
- Red：新增 Nova Lite outgoing tool request contract；目前 request 仍含 `strict: true`，targeted test依缺少相容轉換而失敗。
- Green：只對 exact `amazon.nova-lite-v1:0` 深拷貝 request tool，移除 `strict`、`additionalProperties`、`minLength`、`maxLength`、`minItems`、`maxItems`；其他模型保留既有 strict schema，回應仍通過原有 exact-key、型別、長度與玩家集合 validators。
- Regression：Bedrock／production Worker／async workflow／publisher／PostgreSQL store相關測試全綠；完整 Backend suite exit `0`；Frontend `96/96`。
- Sensitivity：暫時停用 Nova Lite轉換後，新 targeted test重新失敗於 `strict`；還原後通過。
- Rollback／殘餘風險：回復 Green commit即可撤銷；本機測試不能證明實際 Bedrock接受 request。production Worker仍使用舊 image digest `sha256:ede0f8e571824e2b1100a537795825ecdff415b0dbd1fcbc1e8a1ebd50bf1757`，必須先通過 PR CI、獨立 Worker image release與新的單次 Bedrock測試核准，才能重新驗證 AWS E2E。
