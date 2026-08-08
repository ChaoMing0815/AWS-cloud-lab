# FastAPI／FetchGameApi vertical slice 驗證

- 日期：2026-08-08
- 範圍：本機 FastAPI＋瀏覽器前端
- AWS 寫入／資源／費用：無
- LLM：`MockStoryteller`，未呼叫 Bedrock

## 自動測試

後端：`5 passed`。

- `GET /api/v1/health`。
- FastAPI 同源提供 `web/`。
- 建立房間並以 `HttpOnly` local room cookie 恢復。
- 加入玩家與重複 nickname 負面測試。
- room version conflict 回傳 structured `409`。

前端：`12 passed`。

- 原有 Domain、use case 與 `MockGameApi` tests。
- `FetchGameApi` 同源 cookie、room version 與 structured error tests。

## 瀏覽器整合測試

1. FastAPI 提供首頁與 ES modules，畫面顯示「本機 FastAPI 模式」。
2. 初次 smoke test 發現原生 `fetch` 失去 browser binding，顯示 `Illegal invocation`。
3. 修正 `FetchGameApi` 的預設 fetch wrapper 後重新測試。
4. `GET /api/v1/rooms/current` 回傳 demo room，Console errors 為 0。
5. 建立新房間成功：HTTP `201`、六碼 room code、`0 / 5`。
6. 加入「API玩家／沉著的企劃」成功：HTTP `201`、`1 / 5`。
7. 重新整理後 room code、玩家名稱與 `1 / 5` 均保留。
8. Uvicorn access log 顯示靜態檔案與 API requests 均由同一 origin 提供。

## 安全邊界

- Browser 不含 AWS SDK、API key 或 Access Key。
- Session pointer 使用 `HttpOnly`、`SameSite=Lax` cookie；目前只供本機 room 恢復，不代表正式 player／host authorization 已完成。
- Mutation 傳送 room version，後端拒絕 stale version。
- Canonical state 位於 FastAPI memory repository，不在 `localStorage`。
- Storyteller 使用 port／adapter，未呼叫外部 LLM。

## 未完成

- 正式 player／host opaque session、CSRF 與 idempotency key。
- PostgreSQL repository、schema 與 migrations。
- 世界草稿、完整角色配點與 deterministic rules engine。
- `BedrockStoryteller`、model selection、最小 IAM policy、token／cost logs。
- AWS Tier 0 部署與證據。
