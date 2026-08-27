# Tier 2 Story Job Queue Contract

- 狀態：第二階段 local durable contract
- 風險：R3（queue／migration／durable lease）
- 範圍：純本機 domain、application port、memory與PostgreSQL adapter；不接入現行request flow
- 上游依據：Tier 2 累積演進方向、既有 Room aggregate 與 Storyteller port

## 目的與非目標

第一階段固定 Web／API、Story Worker與Data之間的依賴方向，以及非同步story job的identity、狀態與replay規則。第二階段以append-only `002_create_story_jobs.sql`與`PostgresStoryJobQueue`保存同一公開contract。它不改變玩家可見行為，不修改`RoomService`、API route、Storyteller adapter或production composition，也不宣稱distributed exactly-once。

## Cohesive contract

### Identity 與 Room 關聯

- `job_id` 是每筆 queue record 的唯一 identity，由 producer 建立，與業務冪等性分離。
- `operation` 第一階段固定支援 `RESOLVE_ROUND`；後續 operation 必須另以 contract 擴張。
- 每筆 job 綁定 `room_id`、`round_number` 與 enqueue 當下的 `room_version`。三者讓 worker 在真正接線後能拒絕 stale write；本切片不讀寫 Room。
- canonical `idempotency_key` 為 `story:{operation}:{room_id}:round:{round_number}:version:{room_version}`。相同 key 代表同一個業務工作，不代表 transport 只投遞一次。

### Payload ownership

- Web／API producer 擁有 payload schema 與建立時點，enqueue 後 payload 視為 immutable snapshot。
- Story Worker 只能讀取 job snapshot、產生結果，再透過[`tier2-story-resolution.md`](tier2-story-resolution.md)的Data contract進行version-checked commit；不得把queue當Room狀態權威。
- Room repository／Data component 仍是 Room aggregate、round progression 與玩家可見結果的唯一權威。queue 只保存工作生命週期。
- 第一階段 payload 只要求 JSON-compatible mapping；實際 Storyteller input schema 留待接線切片，避免把現行 `Room` aggregate 偷渡成跨組件共享 model。

### 狀態轉移與 replay

```text
PENDING --claim(worker)--> CLAIMED --complete(token, result)--> COMPLETED
   ^                         |
   |---- fail(token) --------|  （attempt 尚未耗盡）
                             +-- fail／lease expiry at max --> DEAD_LETTERED
```

- `enqueue`：新 key 建立 `PENDING` job；相同 key 與相同完整工作內容回傳既有 job，不新增副本；相同 key 但不同 job identity、Room 關聯、operation 或 payload 時拒絕為 conflict。
- `job_id` 與 `idempotency_key` 各自唯一；若一次 enqueue 的兩個 identity 分別解析到不同既有 job，必須拒絕 cross-identity collision。
- `claim`：使用 injected clock 的 aware UTC timestamp 建立 lease，並產生不可猜測的 ownership／fencing token；測試可注入 deterministic token factory，但 production 預設使用 secure random token。
- lease 未到期時，同一 worker replay 回傳相同 token 且不增加 attempt；其他 worker 不可接管。lease 到期後，新 worker 可取得新 token 並增加 attempt，舊 token 立即失效。
- `complete`：只有未到期的目前 token 可完成；相同 token 以相同 result 重複 complete 回傳既有 `COMPLETED` job；不同 token 或 result 必須拒絕，避免 replay 覆寫權威結果。
- `fail`：目前 token 回報失敗後，未達 `max_attempts` 回到 `PENDING`；到達上限則進入 terminal `DEAD_LETTERED`。lease 到期且 attempt 已耗盡時同樣進入 terminal 狀態，不可無限重試。
- `attempt_count` 在首次成功 claim 時增加；同一 owner 的 replay 不增加。
- 找不到 job 時回報 not-found contract error，不將 transport timeout 誤當成工作不存在。

### 失敗、重試與 exactly-once 邊界

- 目前 memory adapter 只模擬 lease timestamp 與 dead-letter 等價狀態，不提供 durable lease、外部 visibility timeout、durable dead-letter queue、process restart recovery 或 multi-process coordination。
- PostgreSQL adapter把job identity、payload snapshot、status、attempt、UTC lease、fencing token、result與terminal failure保存於`story_jobs`；新adapter instance可讀取並以相同CAS規則繼續處理。
- `enqueue`使用`ON CONFLICT DO NOTHING`後鎖定identity rows；claim／expired reclaim／complete／fail都在單一transaction內以`FOR UPDATE`與status、token、lease條件更新。DB constraint拒絕不合法state shape。
- PostgreSQL的partial unique index保護非空ownership token，`job_id`與`idempotency_key`分別唯一；cross-identity collision與stale token一律fail closed。
- transport 可 at-least-once 投遞；producer 負責穩定 idempotency key，queue adapter 負責同 key 去重，worker 負責 claim ownership 與 deterministic completion，Data integration 最終必須以 `room_version` 做 compare-and-set。
- 本地PostgreSQL persistence不是SQS visibility timeout或distributed exactly-once；Data result CAS／inbox-outbox已有未接線local contract，SQS adapter與production wiring仍需後續獨立contract。

## Acceptance criteria

1. Domain 能表達 immutable job identity、Room／round／version 關聯、payload、狀態、owner、attempt 與 completion result。
2. Application 提供 canonical idempotency key 與建立 `PENDING` job 的 factory。
3. `StoryJobQueue` port 固定 enqueue／claim／complete／fail 邊界。
4. Memory與PostgreSQL adapter都通過identity collision、nested snapshot、lease、fencing token、bounded retry與terminal replay正負contract。
5. `002`完整約束identity、Room coordinates、payload、lifecycle、result／failure與UTC timestamps，且不修改`001`。
6. PostgreSQL adapter的核心SQL／transaction contract可離線驗證；明確提供專用DSN時才額外執行restart integration。
7. 現行RoomService、API、Storyteller、Room repository與composition完全不接線且regression全綠。
