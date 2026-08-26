# Tier 2 Story Job 第一階段 Contract

- 狀態：Ready for TDD
- 風險：R2（queue／跨組件 contract）
- 範圍：純本機 domain、application port 與 memory adapter；不接入現行 request flow
- 上游依據：Tier 2 累積演進方向、既有 Room aggregate 與 Storyteller port

## 目的與非目標

本切片先固定 Web／API、Story Worker 與 Data 之間的依賴方向，以及非同步 story job 的 identity、狀態與 replay 規則。它不改變玩家可見行為，不修改 `RoomService`、API route、Storyteller adapter、production composition 或資料庫 schema，也不宣稱已具備跨 process exactly-once。

## Cohesive contract

### Identity 與 Room 關聯

- `job_id` 是每筆 queue record 的唯一 identity，由 producer 建立，與業務冪等性分離。
- `operation` 第一階段固定支援 `RESOLVE_ROUND`；後續 operation 必須另以 contract 擴張。
- 每筆 job 綁定 `room_id`、`round_number` 與 enqueue 當下的 `room_version`。三者讓 worker 在真正接線後能拒絕 stale write；本切片不讀寫 Room。
- canonical `idempotency_key` 為 `story:{operation}:{room_id}:round:{round_number}:version:{room_version}`。相同 key 代表同一個業務工作，不代表 transport 只投遞一次。

### Payload ownership

- Web／API producer 擁有 payload schema 與建立時點，enqueue 後 payload 視為 immutable snapshot。
- Story Worker 只能讀取 job snapshot、產生結果，再透過未來的 Data integration 進行 version-checked commit；不得把 queue 當 Room 狀態權威。
- Room repository／Data component 仍是 Room aggregate、round progression 與玩家可見結果的唯一權威。queue 只保存工作生命週期。
- 第一階段 payload 只要求 JSON-compatible mapping；實際 Storyteller input schema 留待接線切片，避免把現行 `Room` aggregate 偷渡成跨組件共享 model。

### 狀態轉移與 replay

```text
PENDING --claim(worker)--> CLAIMED --complete(worker, result)--> COMPLETED
```

- `enqueue`：新 key 建立 `PENDING` job；相同 key 與相同完整工作內容回傳既有 job，不新增副本；相同 key 但不同 job identity、Room 關聯、operation 或 payload 時拒絕為 conflict。
- `claim`：只有 `PENDING` 可由 worker claim；同一 worker 重複 claim 同一 job 回傳既有 `CLAIMED` job；不同 worker 不可接管；`COMPLETED` 不可再 claim。
- `complete`：只有 owner worker 可完成；相同 worker 以相同 result 重複 complete 回傳既有 `COMPLETED` job；不同 result 或不同 worker 必須拒絕，避免 replay 覆寫權威結果。
- `attempt_count` 在首次成功 claim 時增加；同一 owner 的 replay 不增加。
- 找不到 job 時回報 not-found contract error，不將 transport timeout 誤當成工作不存在。

### 失敗、重試與 exactly-once 邊界

- 目前 memory adapter 不提供 durable lease、visibility timeout、dead-letter、process restart recovery 或 multi-process coordination。
- transport 可 at-least-once 投遞；producer 負責穩定 idempotency key，queue adapter 負責同 key 去重，worker 負責 claim ownership 與 deterministic completion，Data integration 最終必須以 `room_version` 做 compare-and-set。
- worker failure／lease expiry／retry scheduling 與 Data transaction 將在 SQS／durable store 接線前另定 contract；本切片刻意不以 process memory 模擬 production exactly-once。

## Acceptance criteria

1. Domain 能表達 immutable job identity、Room／round／version 關聯、payload、狀態、owner、attempt 與 completion result。
2. Application 提供 canonical idempotency key 與建立 `PENDING` job 的 factory。
3. `StoryJobQueue` port 固定 enqueue／claim／complete 邊界。
4. Memory adapter 通過新建與上述重複 enqueue／claim／complete 的正負 contract。
5. 現行 RoomService、API、Storyteller、repository 與 composition 完全不接線且 regression 全綠。
