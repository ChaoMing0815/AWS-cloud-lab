# LLM recovery 與 Uvicorn process restart：TDD 驗證

- 日期：2026-08-10
- Branch：`codex/llm-recovery-and-process-restart`
- Baseline：`316cde8`
- AWS：未操作
- 真實 LLM／Bedrock：未呼叫，無 API key 或 Access Key

## Acceptance criteria

- `TIMEOUT`、`THROTTLED`、`TRANSIENT_SERVICE_ERROR` 與 `SCHEMA_INVALID` 最多自動重試一次。
- `CONTENT_REJECTED` 不自動重試。
- 每次 retry 使用同一份 canonical resolution draft，不重新擲骰。
- 仍失敗時保存 `RESOLUTION_FAILED`，但不提交進度、危機、星火、action 清除或故事。
- 房主可用新 idempotency key 手動 retry，或以 deterministic fallback 提交既定結果。
- Fallback 不聲稱 LLM 成功，並記錄 `resolution_mode=fallback`。
- 房間與 Host／Player session 可跨真正 Uvicorn OS process restart 還原。

## Baseline

- Backend：`50 passed, 6 skipped`；PostgreSQL integration 因未啟動測試 DB 而明確跳過。
- Frontend：`58 passed`。

## Red／Green

| 切片 | Red | Green |
| --- | --- | --- |
| Storyteller injection | `3465088`：`create_app` 不接受 Storyteller dependency | `4fc8221` |
| Failure taxonomy／bounded retry | `e6da38d`：五項 recovery tests 皆直接拋出 failure | `2c576f7` |
| Deterministic fallback | `e9a80be`：`RoomService.fallback_round` 不存在 | `b257378` |
| Host-only fallback API | `e23a09c`：route 回傳 405 | `8fc4ece` |
| Manual retry | `0d36549`：`RESOLUTION_FAILED` 被 `RESOLVE_NOT_ALLOWED` 拒絕 | `edc4a21` |
| Frontend recovery controls | `1cb2c55`：transport、ViewModel、markup 共 3 項失敗 | `561cf72` |

Fallback API Red 原先把匿名請求預期為 403；route 建立後進入既有授權層，確認專案契約以 401 表示無 session、403 表示已有身份但無權。原 Red 的實際缺口仍是 405；Green 前只校正狀態碼，不放寬 host-only assertion。

## Canonical-state 保護

在兩次 LLM 嘗試皆失敗後，測試逐項比較 failure 前後資料：

- `progress_points`、`danger_points` 不變。
- Character／Spark 不變。
- 玩家 action 不清除。
- `entries` 不新增。
- `dice_results` 完整保留。
- 只新增安全的 failure classification、attempt count、`RESOLUTION_FAILED` 與 room version。

手動 retry 與 fallback 都沿用原 DiceResult；idempotency replay 不會再次加點、扣星火或推進回合。

## Sensitivity

- 暫時把自動嘗試上限由 2 改成 1。
- Recovery suite 8 項中 7 項失敗，包含三類 retryable failure、failure state、fallback API 與 manual retry。
- Mutation 已立即還原，未提交至 Git。

## 真實 process restart

`test_process_restart_e2e.py` 屬既有持久化能力的 runtime verification，不冒充為新增行為的 Red／Green：

1. 以專用 PostgreSQL container 建立空 schema。
2. 啟動第一個 Uvicorn OS process，透過 HTTP API 建房並取得 HttpOnly session cookies。
3. 保存完整 world、角色、Round 3、進度／危機、DiceResult 與故事。
4. 終止第一個 Uvicorn process。
5. 啟動第二個全新 Uvicorn process。
6. 使用原 cookies 取得同一 room，逐項驗證完整 aggregate 與 Host／Player session。

## 最終結果與清理

- Backend：`66 passed`，包含 PostgreSQL contract、migration、application restart 與 Uvicorn process restart。
- Frontend：`60 passed`。
- 已知非阻擋警告：FastAPI `TestClient` 的 Starlette/httpx deprecation。
- `co-story-process-restart-db` 使用 `--rm`，完成後已停止；`docker ps -a` 確認無殘留。
- 測試 DSN／密碼未寫入 repository。

## 尚未涵蓋

- 尚未建立 `BedrockStoryteller`、真實 JSON schema validator、Guardrail 或模型 telemetry adapter。
- `SCHEMA_INVALID` 本階段驗證的是 application recovery contract；未宣稱已完成真實模型 output validation。
- 尚未建立應用 Docker image，因此本階段只勾選 OS process restart，不宣稱 application container restart。
- Persistent idempotency 與 multi-process conditional update 仍依 ADR-0003 留待後續切片。
