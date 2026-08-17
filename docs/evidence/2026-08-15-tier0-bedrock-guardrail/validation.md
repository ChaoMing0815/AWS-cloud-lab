# Tier 0 Bedrock Guardrail Console 驗證摘要

- 日期／方式：2026-08-15；MFA `ming-dev`、AWS Console-first、Tokyo `ap-northeast-1`；未使用 AWS CLI。
- 候選模型：Amazon Nova Lite，model ID `amazon.nova-lite-v1:0`，Serverless、Tokyo in-Region、Converse-compatible；未呼叫模型。
- 標準方案價格基準：每 100 萬 input tokens `US$0.072`、每 100 萬 output tokens `US$0.288`。runtime output ceiling 為 800 tokens；以每次 2,000 input＋800 output 的保守估算，單次約 `US$0.0003744`，4 回合 7 次推論約 `US$0.0027`，不含 Guardrail 評估費。
- Guardrail：`co-story-tier0-safety` 建立完成，status `Ready`，KMS 使用 AWS default，Cross-Region inference profile 為 `apac.guardrail.v1:0`。
- Content filters：Standard tier；Hate High、Insults Medium、Sexual High、Violence Low、Misconduct Low，prompts／responses 均為 Block；Prompt Attack High／Block；只啟用 Text。
- Privacy：EMAIL／PHONE 在 input／output 均 Mask；regex 0。
- 明確停用：Denied topics 0、Profanity disabled、custom words 0、Grounding disabled、Relevance disabled。
- Blocked messages：prompt 與 response 使用不同繁體中文安全訊息。
- 成本／安全邊界：建立過程未 Test、未 Invoke Nova Lite、未發布或驗證 Guardrail version、未授予 EC2 AppRole Bedrock 權限、未啟用 Model Invocation Logging、未訂閱 Marketplace。
- Residual risk：下一批須先發布固定 Guardrail version，再以 exact model／Guardrail ARN 收斂 AppRole，並在明確核准的極小測試預算內做 allow／block／PII mask 三類驗證。
