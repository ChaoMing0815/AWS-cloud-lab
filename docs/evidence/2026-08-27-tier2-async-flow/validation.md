# Tier 2 玩家可見 Async Flow 驗證

- 日期：2026-08-27
- Branch：`codex/tier2-async-flow`
- 治理起點：`5fdb13324b821915e92983fb3ebc881a2ecbcaed`
- 同步main治理修正：`e036e8b`
- 風險：R2
- AWS／production：未操作

## Strict TDD

### Cohesive Red 1：玩家可見API與polling

- Commit：`db87976`
- Backend精確失敗：`create_app()`尚未接受`story_resolution_producer`。
- Frontend精確失敗：`202` envelope未解開，Room沒有`RESOLVING`；60秒後沒有`resolution-delayed`提示。

### Green 1

- Commit：`d6a4752`
- resolve route在async composition回`202 + jobId + room`，保留host session、CSRF、Room version與Idempotency-Key guard。
- 同一request replay只建立一個job；Web request不呼叫Storyteller。
- Fetch adapter解開envelope；GamePage只讀polling，60秒後只顯示延遲提示，不取消、不重送、不自動fallback。

### Cohesive Red 2：獨立Worker process

- Commit：`d492199`
- 精確失敗：snapshot narrator、Worker runner、PostgreSQL available-job query與automatic producer composition均不存在。

### Green 2

- Commit：`c765adb`
- PostgreSQL Web composition只建立`StoryResolutionProducer`，不在Web process內建立Worker。
- local Worker runner每次處理一個available job；production環境拒絕local Mock CLI。
- snapshot narrator只重建公開story context，並支援最終回合ending narration。
- process E2E覆蓋Web process停止、Worker process處理、第二個Worker idle與API restart；只有提供專用PostgreSQL DSN才執行。

## Regression

- Backend：完整`backend/tests`通過；共收集569 cases，結果為`558 passed, 11 skipped`。skip包含未提供專用`CO_STORY_PROCESS_TEST_DATABASE_URL`的真實process／PostgreSQL gate，未以memory double替代。
- Frontend：`96 passed, 0 failed`。
- 受影響Backend targeted：async API、Worker、production composition、PostgreSQL queue、Story Result workflow全綠。
- Branch boundary：`branch_boundary=passed`。
- `git diff --check`：passed。
- 既有Starlette `httpx` deprecation warning未由本切片新增。

## 保留邊界

- 未執行AWS CLI、SSM、S3或Bedrock呼叫。
- 未執行production migration、container build、workflow dispatch或release。
- local Worker固定Mock並fail closed拒絕production；Bedrock Worker、SQS、DLQ、private Worker與AWS E2E留待下一個bounded batch。
