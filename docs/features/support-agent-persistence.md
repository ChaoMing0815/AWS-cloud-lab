# Bounded Support Agent 持久化（PostgreSQL Draft）

- 狀態：Implemented locally (未接 API / UI / Bedrock)
- 上游：ADR-0005、Tier 2 migration 已整併後路徑
- R3 boundary：本批次僅做 PostgreSQL 草稿持久化與 004 migration；提交/外部傳輸仍禁止。

## 目標

在 `codex/support-agent-persistence` 範圍內，將 Phase A 的 `draft_problem_report` 草稿從 memory adapter 擴展為 PostgreSQL 持久化：

1. 使用 `004_create_support_report_drafts.sql` 建表。
2. 實作 `PostgresSupportReportRepository`，支援 idempotent replay。
3. 契約不變：`requires_human_confirmation=true`、`submission_status=local_draft_only`。
4. 保留輸入去敏與欄位級敏感資料不落庫的行為。
5. 提供 restart-safe 驗證：不同 `SupportAgent` 實例同一 input 可取回同一草稿。

## 可驗收行為

- report 寫入前，`report_id`、`idempotency_key`、`reporter_identity_hash`、`payload_fingerprint` 皆為穩定不可變哈希。
- 16 字元草稿前綴（`report_id`）與完整 `idempotency_key` 形成穩定 replay；同一 identity + 同一 normalized 內容必定回傳相同草稿。
- `idempotency_key` diverge（同 idempotency key 但 payload 不同）或 16-hex 前綴 collision（不同 payload 但 `report_id` 相同）必定 `SupportReportConflict`。
- adapter 回傳內容與 application 回傳前需一致比對，不一致即 `corrupt_report_contract`。
- `payload_version`, `requires_human_confirmation`, `submission_status`, `reporter_identity_hash`, `idempotency_key` 為固定長度/值形狀；DB constraint 失配即 fail closed。

## 安全限制

- 不接受 raw description、raw identity；草稿僅保留 sanitized structured fields。
- 不允許保存 `session_token/csrf/password/AWS credential/DATABASE_URL/runtime secret/JWT/PostgreSQL URL`。
- 沒有提供 `CO_STORY_SUPPORT_TEST_DATABASE_URL` 時，restart / 併發/真 DB 測試必須明確 skip，不宣稱 durability。

## 目前未接範圍

- API/route、Web、Bedrock、外部 issue tracker/email、`main.py` composition、dependency manifest、`RoomRepository`、`migration runner`。
- 任何 production deploy 前置都需另作 migration rollback / readiness 與回退 gate，且本 PR 只會 create migration，不啟動 release。
