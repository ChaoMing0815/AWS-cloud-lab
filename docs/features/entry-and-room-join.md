# Feature Spec：正式入口與房間加入

- 狀態：Approved for TDD
- Owner：Product／Engineer／QA
- Source of Truth：是，僅限正式入口與加入流程
- Depends on：[MVP Spec](../specs/text-rpg-mvp-spec.md)、[User Flow](../product/user-flow.md)、[Screen States](../product/screen-states.md)、[ADR-0002](../decisions/0002-adopt-clean-frontend-architecture.md)
- 核准依據：[2026-08-09 approval log](../governance/approval-log.md)
- 最後檢視：2026-08-09

## 目標

讓沒有 session 的使用者從正式首頁選擇建立、加入或教學 Demo；移除正式路徑自動進入 `BONUS7` 的行為。房主建房時同時成為第一位玩家。

## 範圍

- `/` 正式首頁與輕量 router。
- 建立房間時建立 Host＋Player 身份。
- 以 room code＋暱稱原子性加入房間。
- 有效 session 的繼續入口。
- `/demo` 與正式資料完全隔離。

## 不在本切片

- 完整角色表單與 Lobby start gate。
- 跨裝置轉移碼、session expiry、刪除與七天清理。
- Polling backoff。
- PostgreSQL、真實 LLM 或 AWS 寫入。
- 既有骰子、星火、進度與結局規則變更。

## Acceptance Criteria

1. 無有效 session 開啟 `/` 時，只顯示建立、加入與次要 Demo 入口，不載入任何 Demo 房間。
2. 房主以合法暱稱建立房間後，後端原子性建立 Room、Host session、第一位 Player 與其 Player session；該玩家計入 3–5 人限制。
3. 建房成功後進入世界設定；世界確認後才能進 Lobby 並分享可加入的 room code。
4. 玩家以 room code＋暱稱加入；後端原子性拒絕格式錯誤、不存在、非 Lobby、已滿與重複暱稱。
5. 加入成功後建立 Player session 並進入該房 Lobby，不依賴瀏覽器先載入某個 current room。
6. 有效 session 開啟首頁時顯示「繼續目前遊戲」，並依 canonical room state 導向 setup、lobby、play 或 ending。
7. `/demo` 使用固定 Mock 資料，不呼叫正式 API、不建立正式 session、不保存進度，並顯示教學標示。
8. 深層 URL 重新整理仍可由 FastAPI 提供 App shell；無效路由顯示可回首頁的 404 狀態。

## 邏輯 API Contract

### 建立房間

```http
POST /api/v1/rooms
Idempotency-Key: <uuid>
Content-Type: application/json

{"nickname":"房主玩家暱稱"}
```

Response 設定獨立 Host／Player `HttpOnly` cookie，body 回傳 room view、目前 player view 與 CSRF 資料。前端不能提交 `player_id`。

### 加入房間

```http
POST /api/v1/rooms:join
Idempotency-Key: <uuid>
Content-Type: application/json

{"room_code":"ABC123","nickname":"玩家暱稱"}
```

後端在同一 operation 完成 room lookup、狀態／容量／暱稱檢查與 Player session 建立；不先提供匿名的房間詳細資料查詢。

### 讀取目前 session

`GET /api/v1/session/current` 回傳匿名、Host＋Player 或 Player 的安全摘要，以及可繼續的 room route；不得回傳 cookie、token hash 或其他玩家私密 action。

## 錯誤代碼最低集合

- `ROOM_CODE_INVALID`
- `ROOM_NOT_FOUND`
- `ROOM_NOT_JOINABLE`
- `ROOM_FULL`
- `NICKNAME_DUPLICATE`
- `SESSION_NOT_FOUND`
- `IDEMPOTENCY_KEY_REQUIRED`
- `IDEMPOTENCY_KEY_REUSED`

錯誤 body 必須提供穩定 code 與 request ID，不回傳 stack trace。

## TDD 切片順序

1. Red：無 session 首頁不載入 Demo；Green：LandingPage／router 最小行為。
2. Red：建立房間同時建立 Host player；Green：domain／service／route 最小變更。
3. Red：依 room code 原子性加入與拒絕案例；Green：repository lookup／API／adapter。
4. Red：session continue route；Green：session summary 與導航。
5. Red：`/demo` 不呼叫正式 API；Green：隔離的 Mock composition。
6. Refactor：拆分現有大型 `GamePage`，每一步保持 regression 全綠。

每個 Red 必須因缺少目標行為失敗，不得以 import／fixture 錯誤充當 Red。

## 完成證據

- Backend／frontend targeted tests 與完整 regression 全綠。
- 建立、加入的正面與各拒絕案例 API 證據。
- Browser 驗證 `/`、建立、加入、繼續、`/demo` 與 deep-link refresh。
- Browser Console 無未處理錯誤。
- README、task list、checkpoints、handoff 與 evidence 同步。

## Rollback

入口切片若未完成，不合併至 `main`。Rollback 只回復本切片 router／page／API wiring；不得以恢復正式路徑的 Demo fallback 作為修復方式。
