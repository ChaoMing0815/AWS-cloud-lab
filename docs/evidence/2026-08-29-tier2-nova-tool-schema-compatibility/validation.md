# Tier 2 Nova Lite tool schema 相容性驗證

- 範圍／風險：修正 production Story Worker 對 `amazon.nova-lite-v1:0` 的 Bedrock Converse tool request；R3。Web runtime 維持 `sync`，不變更 IAM、Guardrail、Region、model ID、SQS、CloudFormation 或資料 schema。
- AWS 失敗證據：exactly-one job 完成 typed JSONB producer、publisher、SQS dispatch、Worker claim 與 completion，但 room 結果為 `INVALID_MODEL`；兩台 Worker 均為 `ap-northeast-1`、`amazon.nova-lite-v1:0`、Guardrail version `1`、async，服務與 container healthy。測試 DB marker 已清除，主佇列與 DLQ 的 available／in-flight 四項皆為 `0`。
- 上游依據：AWS Nova Lite model card確認 Tokyo、Converse、Guardrails與client-side tool calling受支援，但 Structured outputs不受支援；AWS Nova v1 tool schema文件與troubleshooting列出 tool schema subset；Bedrock structured-output文件列出不支援的字串長度 constraints。
- Red：新增 Nova Lite outgoing tool request contract；目前 request 仍含 `strict: true`，targeted test依缺少相容轉換而失敗。
- Green：只對 exact `amazon.nova-lite-v1:0` 深拷貝 request tool，移除 `strict`、`additionalProperties`、`minLength`、`maxLength`、`minItems`、`maxItems`；其他模型保留既有 strict schema，回應仍通過原有 exact-key、型別、長度與玩家集合 validators。
- Regression：Bedrock／production Worker／async workflow／publisher／PostgreSQL store相關測試全綠；完整 Backend suite exit `0`；Frontend `96/96`。
- Sensitivity：暫時停用 Nova Lite轉換後，新 targeted test重新失敗於 `strict`；還原後通過。
- Integration：PR #56四項CI全綠並合併為exact main `98ded43cad36a59c020f3937db0d360d019749f8`。Worker image run `33257141550`完成ARM64 build／immutable push、exact-digest Trivy與manifest，產生`sha256:94ff5d2c073542393d4e82d1b1c620ee2653730a78a9c655fbf13694024bf8f0`。
- Production rollout：使用者以bounded SSM精確選取兩台private Worker，由previous `sha256:ede0f8e571824e2b1100a537795825ecdff415b0dbd1fcbc1e8a1ebd50bf1757`更新；兩台皆回`nova_lite_schema=compatible`、service active、container running、restart `0`、mode async。部署後兩台皆執行registry logout並確認credential absent；Web仍為`sync`。
- Rollback／殘餘風險：每台release均保留previous digest rollback；local／CI與部署健康不能證明實際Bedrock接受request。升版後未建立test job、未送SQS或呼叫Bedrock，必須取得新的exactly-one單次測試核准後才能宣稱AWS E2E通過。
