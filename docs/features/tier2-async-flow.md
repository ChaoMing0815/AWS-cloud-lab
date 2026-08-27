# Tier 2 玩家可見非同步回合結算

- 狀態：Local implementation complete；等待整合 review
- 風險：R2（跨 API、PostgreSQL、獨立 process 與可觀察 UI）
- 上游依據：Accepted ADR-0004、2026-08-27 使用者核准
- 非部署聲明：本切片未執行 production migration、AWS、SSM、S3或Bedrock

## 玩家可見行為

1. 房主送出回合結算後，API完成host session、CSRF、Room version與Idempotency-Key驗證，再以同一PostgreSQL transaction把Room改為`RESOLVING`並建立immutable StoryJob。
2. API回`202 Accepted`，payload包含opaque `jobId`與canonical Room；Web顯示「AI 正在整理劇情」，不等待Storyteller完成。
3. Web沿用`GET /api/v1/rooms/current`每3秒讀取canonical Room。60秒仍為`RESOLVING`時顯示延遲提示，但不取消、不重送job、不自動fallback，也不中止room polling。
4. 獨立Worker process從PostgreSQL durable queue取得一個available job，以session-free snapshot呼叫Storyteller，再依既有inbox／outbox contract提交結果。
5. 成功後所有玩家在下一次poll看到新敘事與下一回合／結局；terminal Storyteller failure寫成`RESOLUTION_FAILED`，只有房主看到既有人工retry與deterministic fallback控制。

## API contract

成功回應：

```json
{
  "jobId": "opaque-server-generated-id",
  "room": {
    "status": "RESOLVING",
    "version": 8
  }
}
```

- `jobId`只作client correlation，不授予Worker、Room或管理權限。
- 同一Idempotency-Key與相同body重送，回相同job；更改body則沿用既有`IDEMPOTENCY_KEY_REUSED`防線。
- Web process不持有Worker loop，也不在resolve request內呼叫Storyteller。
- 既有memory／Demo composition保留同步路徑；只有由`DATABASE_URL`建立的PostgreSQL composition自動啟用async producer。

## Local Worker contract

- `python -m app.workers.story_resolution_worker`只處理一個available job並退出，輸出只有`worker_result=processed|idle`。
- 本切片的CLI固定使用`MockStoryteller`並拒絕`CO_STORY_ENV=production`，避免把尚未核准的本地worker誤當production Bedrock Worker。
- snapshot narrator只重建world、最近公開敘事、公開角色敘事資料、行動與canonical dice結果；不建立session、CSRF、cookie、transfer code或runtime secret。
- 真實process gate必須使用明確的`CO_STORY_PROCESS_TEST_DATABASE_URL`；未提供時測試標記skip。

## 非目標與下一步

- 不建立SQS、DLQ、private Worker EC2／ECS、lease heartbeat或AWS網段。
- 不執行`002`／`003` production migration，不修改Docker、workflow、IaC或release文件。
- 不把本機Mock Worker宣稱為Nova Lite或AWS E2E。
- 整合後下一批才設計SQS transport、private Worker／Data Security Group、production Worker runtime與bounded deployment envelope。
