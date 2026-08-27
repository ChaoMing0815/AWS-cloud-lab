# Bounded Support Agent Phase A

- 狀態：Implemented locally
- 上游：ADR-0005、正式 MVP Spec
- 風險：R2；tool authorization、prompt injection 與敏感資料採 R3 驗證深度

## 目標與範圍

Phase A 建立尚未接入產品的 Support Agent 核心，只提供兩個固定 capability：

1. `lookup_game_rules`：從版本化 `game_rules.json` 找出唯一有根據的規則，原樣回傳 canonical content，並附 stable rule ID、title、source section 與 source version。查無資料或同時命中多筆時回 `unsupported`，不推測答案。
2. `draft_problem_report`：把本機敘述整理為 `category`、`summary`、`reproduction_steps`、`expected_behavior` 與 `actual_behavior`。草稿固定為 `requires_human_confirmation=true`、`submission_status=local_draft_only`。

本切片沒有 API、Web UI、PostgreSQL、GitHub Issue、Email、LangChain、Bedrock、CloudWatch 或 AWS 整合，也不會外部傳輸或提交問題單。

## 可驗收行為

- Model 只提出 `{tool, arguments}`；application 驗證 exact top-level schema、固定 tool allowlist、exact arguments 及原始輸入一致性後才執行。
- `lookup_game_rules` 只接受單一命中的 allowlisted rule record；application 再核對回答、引用與 knowledge record 完全一致。
- unknown tool、額外或遺漏參數、malformed model output、prompt injection、要求忽略或改寫規則一律 fail closed。
- 敏感內容在送入 model proposal 前清理，草稿與 repository 也只能接觸清理後資料。範圍含 cookie、session／CSRF token、password、AWS credential、`DATABASE_URL`、runtime secret、Bearer token 與常見 credential shape。
- 同一 caller-owned identity 與正規化內容形成穩定 idempotency key；重送取得同一份本機草稿。identity 只保存 SHA-256 digest。
- memory repository 只供 test／local 使用，明確標示非 durable，不宣稱 process restart 或 multi-process 保證。

## 延後整合

必須等 Tier 2 PR 合併並取得新的 path policy 後，才能設計 migration、PostgreSQL repository、API schema／route、production composition、Web UI、Bedrock adapter、observability、rate limiting 或正式 submit tool。任何外部提交仍須獨立授權與再次人工確認。
