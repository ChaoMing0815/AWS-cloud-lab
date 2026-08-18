# Tier 0 真實 Guardrail／Bedrock smoke 驗證

## Batch 7 邊界

- 2026-08-18 使用者已明確核准 Batch 7。
- 固定 Guardrail version `1`、Nova Lite Standard、APAC geographic processing；最多 3 次 model invocation、3 次 synthetic Guardrail evaluation，成本硬上限 `US$0.05`。
- 只使用虛構／合成資料；不啟用 invocation logging、不使用 AWS CLI、不新增 AWS resource、IAM 或固定費用。

## ApplyGuardrail 結果

- 從 Console 開啟的 SSM Session，以既有 application virtualenv、SDK 與 instance role 執行 exactly 3 次 `ApplyGuardrail`；此 API 不呼叫 foundation model。
- Benign input：action `NONE`。
- Harmful input：action `GUARDRAIL_INTERVENED`。
- Synthetic EMAIL／PHONE：action `GUARDRAIL_INTERVENED`，輸出以 `{EMAIL}`／`{PHONE}` mask，原值未保留。
- Usage：content policy `3` text units；sensitive information policy `3` text units。
- 依官方單價估算：`3 × 0.15/1000 + 3 × 0.10/1000 = US$0.00075`。

## 尚待驗證

- 公開 HTTPS 首次真實世界生成已送達 Nova Lite，CloudWatch 出現該 ModelId 的
  `Invocations`、`InputTokenCount` 與 `OutputTokenCount`，沒有 client／server error
  metric；應用 API 回傳 `503`，生成次數由 2 減為 1，但草稿未保存。原始 access
  line 含 client IP 與 room UUID，未收入證據。
- 本機已以 TDD 修正 Nova JSON schema 指示、固定 `temperature=0`、接受只有 JSON
  code fence 的合法輸出，並對 HTML／JavaScript 回應加入 `Cache-Control: no-store`；
  修正版 `tier0-20260818-d9c8f4e` 尚未部署，最後一次世界生成額度保留。
- 三個獨立 Browser session 加入同房、建立角色並完成一個完整回合。
- 真實 storyteller 結算、private RDS refresh、smoke room cleanup 與 Batch 後成本檢查。
