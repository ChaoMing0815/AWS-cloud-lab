# Tier 2 Story Resolution Inbox／Outbox Contract

- 狀態：第三階段 local application contract
- 風險：R3（Room CAS、migration、fencing、transaction rollback）
- 上游依據：Accepted ADR-0004
- 範圍：未接 route、Storyteller adapter與production composition的純本機切片

## Producer transaction

`begin_resolution` 在同一個PostgreSQL transaction內先以stable idempotency key查找replay，再鎖定Room。Room必須符合expected version、round與現行resolve狀態規則；成功後轉為`RESOLVING`、version加一，並在同transaction插入`story_jobs`。Room或job任一寫入失敗都必須整批rollback。

Snapshot只包含world、最近公開故事、回合與canonical deltas、玩家行動、公開角色敘事資料及固定骰點。不得包含host/player session、hash、CSRF、cookie、transfer code或完整Room aggregate；建立後由producer/job各自deep copy，外部nested mutation不得改變已封存payload。

## Worker contract

- Worker只接收`job_id`、worker identity與job snapshot，無任何玩家或host session參數。
- 每次claim先查result inbox；已有receipt時跳過Storyteller與Room mutation，只重送completion。
- 每次claim最多呼叫Storyteller一次。retryable failure在未達上max attempts時交回durable queue；non-retryable或最後attempt形成terminal failure result。
- Data transaction成功commit後才可`queue.complete`。Data rollback不得ack。

## Result transaction與replay

Data transaction先鎖定`story_jobs`，比對完整claim identity、ownership token、attempt與aware UTC lease，再查inbox與鎖定Room。相同job與相同fingerprint回傳原receipt；不同result、過期lease、舊token或被竄改的claim coordinates一律fail closed。

Room的version、round或`RESOLVING`狀態不符時，寫入terminal `stale` receipt與completion outbox，但不修改Room。符合時只套用一次與現行同步resolve相同的回合規則，同transaction寫入Room、`story_result_inbox`與`story_completion_outbox`。

Data commit後若queue completion失敗，lease到期後的新claim讀取已有receipt、將outbox更新為新token，再重送同一completion payload；Room不得再套用。queue completion成功但dispatch marker寫入失敗時，以原token與同payload的terminal replay完成收斂。

## Schema與非目標

Append-only `003_create_story_resolution_results.sql`建立inbox/outbox identity、SHA-256 canonical fingerprint、result/outcome、Room version before/after、ownership token、UTC timestamps與pending-dispatch index；不修改`001`或`002`。

本切片不接FastAPI route、Web、`main.py`、Storyteller adapter、SQS、visibility heartbeat、真正DLQ、AWS E2E或production migration，也不宣稱distributed exactly-once。
