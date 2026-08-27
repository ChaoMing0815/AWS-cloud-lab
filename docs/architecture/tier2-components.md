# Tier 2 三組件架構與本地一致性邊界

- 狀態：第四階段 local async API／Worker process contract
- 範圍：Web／API → Story Worker → Data 的本機接線；尚未 production 部署
- 對應 Feature：[`tier2-story-jobs.md`](../features/tier2-story-jobs.md)、[`tier2-story-resolution.md`](../features/tier2-story-resolution.md)、[`tier2-async-flow.md`](../features/tier2-async-flow.md)

## Current monolith

目前 FastAPI request 由 `RoomService` 同步協調全部工作：讀取 Room aggregate、驗證狀態與版本、直接呼叫 `Storyteller`、套用遊戲規則，再保存 Room。`main.create_app` 在同一 process 組裝 `RoomRepository`、`Storyteller` 與 process-memory idempotency store。

```mermaid
flowchart LR
    Browser -->|HTTPS 同步| API[FastAPI routes]
    API -->|同步 method call| RS[RoomService]
    RS -->|同步 read / write| Repo[RoomRepository]
    RS -->|同步 LLM call| ST[Storyteller]
    Repo --> DB[(PostgreSQL / memory)]
    ST --> Model[Bedrock / mock]
```

此路徑的 Room repository 是狀態權威，但 request latency 與 Storyteller latency 綁定，也尚無 durable job、worker ownership 或跨 process idempotency contract。

## Target components

Tier 2 目標把部署責任分成 Web／API、Story Worker、Data 三個 component，依賴只朝 application ports 與明確訊息 contract，不共享 adapter implementation。

```mermaid
flowchart LR
    Browser -->|HTTPS 同步| Web[Web / API]
    Web -->|enqueue StoryJob\n非同步邊界| Queue[(Story job queue)]
    Worker[Story Worker] -->|claim / complete| Queue
    Worker -->|同步 Storyteller port| Model[Storyteller adapter]
    Web -->|versioned command / query| Data[Data component]
    Worker -->|version-checked result commit| Data
    Data --> DB[(Room authority)]
```

第一階段實作`StoryJob` domain與memory contract double，第二階段新增PostgreSQL durable queue。第三階段建立同DB producer transaction、sanitized snapshot、Story Worker application contract與result inbox／completion outbox。第四階段讓PostgreSQL Web composition以`202`接producer，並提供獨立local Worker process與Web polling；第五階段把 production composition 導向既有Bedrock能力，為終局採用單次 composite tool，維持非終局單一 round invocation。圖仍不是AWS已部署宣告。

## 邊界與責任

| 邊界 | 呼叫型態 | Producer／caller 責任 | Consumer／authority 責任 |
| --- | --- | --- | --- |
| Browser → Web／API | 同步 HTTPS | session、CSRF、expected Room version | 驗證 command，回傳玩家可見狀態 |
| Web／API → queue | 非同步 enqueue | 建立唯一 `job_id`、穩定 idempotency key、immutable payload snapshot | 以 key 去重並保存 job lifecycle |
| Worker → queue | claim／complete／fail | 穩定 worker identity、保存目前 fencing token、replay-safe completion | UTC lease、token fencing、bounded attempts 與完成結果不可覆寫 |
| Web／Worker → Data | 同步或明確 command（後續決定） | 傳入 `room_id` 與 expected version | Room aggregate、round progression、玩家可見結果的唯一權威 |
| Worker → Storyteller | 同步 adapter call | 只使用 job snapshot，分類 retryable failure | 產生敘事，不直接改 Room 或 queue |

## Failure、retry 與 idempotency

- Transport 以 at-least-once 為設計前提；不得從 memory test double 推論 production exactly-once。
- Producer 以 operation／Room／round／version 建立 canonical idempotency key。相同內容重送回既有 job，不同內容重用 key 必須拒絕。
- Queue 負責 `job_id`／idempotency key 雙重唯一性、claim ownership、attempt 計數與 completion replay；cross-identity collision 一律拒絕。
- Memory contract 以 injected clock 計算 aware UTC lease，以 secure random 或測試注入的唯一 token 作 fencing。未到期的 owner replay 不增加 attempt；到期 reclaim 會換 token，使舊 worker 不得 complete。
- Worker 明確 fail 或 lease expiry 達 `max_attempts` 時進入 `DEAD_LETTERED` 等價 terminal 狀態；本地狀態只驗證 bounded retry contract，不是 durable DLQ。
- PostgreSQL adapter以單一transaction鎖定job row，再以status／ownership token／lease timestamp做條件UPDATE；transaction exception由driver rollback，不留下部分lifecycle mutation。
- `002_create_story_jobs`（已完成）保存payload snapshot、Room／round／version關聯、attempt、result／failure與timestamps；state-shape CHECK與unique indexes是application guard以外的第二層防線。production worker 切片新增 `resolve_round_and_ending` 的 single-converse composite，將終局 round 與 ending 合併在同一筆工具輸出中。
- Process restart後新adapter可延續未到期lease、到期reclaim及terminal replay；這仍是PostgreSQL-backed at-least-once contract，不等同SQS或distributed exactly-once。
- 第三階段local Data contract以Room version CAS、job fencing token與UTC lease防止stale result；只有Data commit成功後才可形成canonical state與queue completion intent。
- SQS visibility timeout 與 ownership token 的 durable mapping、retry delay、真正 DLQ、poison payload 與 process restart recovery尚未定案。導入 durable queue／store 前必須另寫 integration contract 與 failure tests。
- `003_create_story_resolution_results.sql`將result fingerprint、terminal stale/applied/failed receipt與completion intent持久化。Data transaction必須先commit，再由Worker ack queue；commit後ack失敗可在reclaim後跳過Storyteller與Room mutation，只重送completion。

## 第四階段接線與刻意保留項目

- PostgreSQL composition的FastAPI resolve route已接producer並回`202`；memory／Demo composition維持同步路徑。
- local Worker process使用session-free snapshot narrator與`MockStoryteller`，Web process不內嵌Worker。
- PostgreSQL Room、`story_jobs`、result inbox與completion outbox已具本機process gate；production尚未執行`002`／`003`。
- Bedrock Worker adapter、SQS、DLQ、visibility heartbeat、private subnet Worker、container／CI/CD調整與AWS E2E仍未接線。
