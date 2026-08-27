# ADR-0004：採用 replay-safe Story Result Inbox／Completion Outbox

- 狀態：Accepted
- 日期：2026-08-27
- 決策者：專題使用者／整合 task
- 範圍：Tier 2 Web／API、Story Worker、Data 與 durable StoryJob 的一致性邊界

## 背景

目前`RoomService.resolve_round`在單一HTTP request內同步呼叫`Storyteller`並保存Room。已完成的`PostgresStoryJobQueue`與`PostgresRoomRepository`各自管理connection與transaction；直接依序呼叫會在Room mutation與job lifecycle之間形成dual-write gap。Worker若在Data commit前後中止，也可能造成結果重複套用或job永遠未完成。

完整`Room`aggregate包含host／player session hash、CSRF與transfer code等不屬於Worker的資料，因此不得直接序列化成job payload。Transport與Worker皆以at-least-once為前提，不宣稱distributed exactly-once。

## 決策

Tier 2下一個本地切片採用下列邊界，且第一批不接API route、Web UI或production composition：

1. Producer在同一PostgreSQL transaction內鎖定Room，以expected version做CAS，將狀態設為`RESOLVING`、版本增加，建立不含session／CSRF／cookie／transfer code的immutable Storyteller snapshot，並插入對應`story_jobs`。
2. Worker只接收job snapshot、worker identity與fencing token；不接收玩家或host session。每次claim只呼叫Storyteller一次，retryable failure交回durable retry policy。
3. Data result transaction先驗證job ownership token、lease與Room version，再只套用一次既有回合規則，同transaction寫入result inbox與completion outbox。
4. Queue completion只能發生在Data transaction commit之後。Data rollback時不得ack；Data commit後若completion失敗，由reclaim／replay讀取inbox，跳過Storyteller與Room mutation，只重送completion。
5. 相同job與相同result fingerprint的replay回傳既有receipt；相同job但不同result必須fail closed。stale Room version形成terminal stale receipt且不得修改Room。
6. Append-only `003_create_story_resolution_results.sql`保存inbox／outbox的identity、fingerprint、UTC timestamps、dispatch state與必要外鍵／state-shape約束；不得修改`001`或`002`。

## 不在本決策內

- 不決定public resolve route是否改回`202 Accepted`、是否公開`jobId`、Web polling／timeout／fallback UX。
- 不接SQS receipt handle、visibility timeout、lease heartbeat、真正DLQ或private Worker AWS部署。
- 不執行production migration或部署，也不改變現行同步遊玩流程。

上述玩家可見API差異與AWS資源會在本地一致性contract全綠後分別形成新的核准批次。

## 結果與取捨

- 優點：明確涵蓋duplicate delivery、stale worker、Data rollback、commit後ack失敗與process restart；未來SQS adapter可沿用相同application contract。
- 代價：新增inbox／outbox schema、replay與cleanup責任，測試需涵蓋transaction fault injection與跨adapter restart。
- Producer現階段可利用Room與story_jobs位於同一PostgreSQL的原子transaction；未來改由SQS承接transport時，producer端需再加入transactional outbox／dispatcher，但不改授權與snapshot contract。

## 本地實作結果

第三階段以`StoryResolutionStore`、未接線`StoryResolutionWorker`、memory transaction double與`PostgresStoryResolutionStore`實作本決策。`003_create_story_resolution_results.sql`是append-only migration；現行同步`RoomService.resolve_round`只抽出並共用既有round-result規則，route、retry與玩家可見結果不變。此狀態仍是repo-local at-least-once contract，不代表production migration、SQS或distributed exactly-once已完成。
