# Bounded Support Agent 核心（歷史切片）

- 狀態：Superseded as current status；核心已由 integration feature 接入並部署 production
- 上游：ADR-0005、正式 MVP Spec
- 風險：R2；tool authorization、prompt injection 與敏感資料採 R3 驗證深度

## 目標與範圍

本文件記錄最初本機核心切片；現在的 production 狀態以 [`CURRENT`](../handoffs/CURRENT.md) 與 [Support Agent integration](support-agent-integration.md) 為準。核心提供兩個固定 capability：

1. `lookup_game_rules`：從版本化 `game_rules.json` 找出唯一有根據的規則，原樣回傳 canonical content，並附 stable rule ID、title、source section 與 source version。查無資料或同時命中多筆時回 `unsupported`，不推測答案。
2. `draft_problem_report`：把本機敘述整理為 `category`、`summary`、`reproduction_steps`、`expected_behavior` 與 `actual_behavior`。草稿固定為 `requires_human_confirmation=true`、`submission_status=local_draft_only`。

最初切片沒有 API、Web UI 或 PostgreSQL；後續已接入 API、Web UI、PostgreSQL 與既有 deployment pipeline。已部署範圍仍沒有 GitHub Issue、Email、LangChain、Bedrock、RAG 或 external submit。

## 可驗收行為

- Model 只提出 `{tool, arguments}`；application 驗證 exact top-level schema、固定 tool allowlist、exact arguments 及原始輸入一致性後才執行。
- `lookup_game_rules` 只接受單一命中的 allowlisted rule record；application 再核對回答、引用與 knowledge record 完全一致。
- unknown tool、額外或遺漏參數、malformed model output、prompt injection、要求忽略或改寫規則一律 fail closed。
- 敏感內容在送入 model proposal 前清理，草稿與 repository 也只能接觸清理後資料。範圍含 cookie、session／CSRF token、password、AWS credential、`DATABASE_URL`、runtime secret、Bearer token 與常見 credential shape。
- 同一 caller-owned identity 與正規化內容形成穩定 idempotency key；重送取得同一份本機草稿。identity 只保存 SHA-256 digest。
- memory repository 只供 test／local 使用，明確標示非 durable，不宣稱 process restart 或 multi-process 保證。

## 後續整合狀態

Tier 2、PostgreSQL persistence／durability、API／session／CSRF／輸入上限／rate limit、Web UI 與 production release 均已完成。Bedrock adapter、RAG、observability 擴張與正式 submit tool 不在已部署的 bounded scope；任何外部提交仍須獨立授權與再次人工確認。
