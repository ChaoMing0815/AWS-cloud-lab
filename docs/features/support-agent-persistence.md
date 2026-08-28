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
- application、memory adapter 與 PostgreSQL adapter 重用同一純 validator；application 在 repository 前與回傳後驗證，adapter 在任何狀態變更、連線或 SQL parameters 前驗證。
- `payload_version`, `requires_human_confirmation`, `submission_status`, `reporter_identity_hash`, `idempotency_key` 為固定值或完整小寫 hex 形狀；application validator 與 DB `CHECK` 都要求 `report_id` 精確等於 idempotency key 前 16 碼，payload fingerprint 必須重新計算一致，DB 回傳列也需通過 validator，否則 fail closed。
- 所有結構化欄位必須已去敏；既有 `[REDACTED]` marker 可保留。本批不新增內容長度或步驟數上限，`reproduction_steps` 只要求非空且沒有 `NULL`／空字串元素。

## 安全限制

- 不接受 raw description、raw identity；草稿僅保留 sanitized structured fields。
- 不允許保存 `session_token/csrf/password/AWS credential/DATABASE_URL/runtime secret/JWT/PostgreSQL URL`。
- 沒有提供 `CO_STORY_SUPPORT_TEST_DATABASE_URL` 時，restart／真 DB 測試必須明確skip。2026-08-28已以一次性 localhost PostgreSQL 16通過 adapter／process restart 與真實 parallel-write contract；並行證據的範圍與限制見下一節。

## 已驗證的並行持久化語意

- 2026-08-28 以一次性、無 volume、僅綁定 localhost 的 PostgreSQL 16 容器驗證。兩個獨立 repository writer 各自建立 PostgreSQL connection，透過 pre-INSERT barrier 同步；winning `INSERT` 在資料庫端暫停，使 competing `ON CONFLICT` 實際與其重疊。
- 相同正規化草稿與 identity 會收斂為同一 canonical row；相同 idempotency key 的不同 payload 與人工相同 16-hex report ID prefix 的不同 payload 都保留一列並回 `SupportReportConflict`。
- 每種競態案例均驗證 row count、固定 state、hash／identity constraint 形狀，以及新 repository instance 的 replay。此為本機非 production durability evidence，不代表 production schema 已啟用或 Support Agent 已接入 API／UI。

## 目前未接範圍

- API/route、Web、Bedrock、外部 issue tracker/email、`main.py` composition、dependency manifest、`RoomRepository`、`migration runner`。
- 任何 production deploy 前置都需另作 migration rollback / readiness 與回退 gate，且本 PR 只會 create migration，不啟動 release。Production bridge 已驗證 active，但 schema 尚未 activation。
