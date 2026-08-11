# Session lifecycle 與角色轉移

- 狀態：Proposed for approval
- Owner：Product／Engineer／QA
- 已核准來源：[正式 MVP Spec](../specs/text-rpg-mvp-spec.md)、[產品核准紀錄](../governance/approval-log.md)
- Depends on：[Session／CSRF／Idempotency 設計](../architecture/session-and-idempotency.md)、[本機 MVP Test Plan](../qa/local-mvp-test-plan.md)、[測試策略](../testing-strategy.md)
- 最後檢視：2026-08-11

## 目標

讓同一瀏覽器可在有效期限內安全恢復角色；過期或被重新指派的 session 不能繼續讀取或修改房間。跨裝置取回角色必須先由房主核准，使用短效、一次性 transfer code，且成功後立即撤銷舊 Player session。

## 已核准且可直接約束實作的行為

1. Host／Player 使用不同 opaque session；room code 與 local room pointer 都不是授權。
2. Token 至少具 128-bit entropy，server 只保存 hash；Cookie 使用 `HttpOnly`、HTTPS `Secure`、`SameSite=Lax` 與合理期限。
3. 進行中房間在最後一次核准活動後 7 天到期；完成房間在結局後保留 7 天；session 不得晚於房間到期。
4. 跨裝置重新指派必須由房主核准；transfer code 有效 10 分鐘且只能使用一次。
5. 成功重新指派後，舊 Player session 立即失效。
6. 錯誤、過期、錯 room／player、replay 與 concurrent redeem 必須拒絕；不得保存明文 session 或 transfer code。

## 2026-08-11 已完成的安全前置

- `GET /api/v1/rooms/current` 在回傳房間前驗證 Host／Player member session；只有 local room pointer 回傳 `401 SESSION_NOT_FOUND`。
- `CO_STORY_COOKIE_SECURE=true` 時，local room、Host 與 Player cookie 全部帶 `Secure`；本機 HTTP 預設維持 `False`。

這兩項不代表 server-side expiry 或角色轉移已完成。

## 建議核准的精確 contract

### 時間與到期

1. 所有時間使用 UTC，application 透過可注入 `Clock` 取得現在時間；測試不得使用 `sleep`。
2. `now >= expires_at` 即視為過期。
3. 有效加入、action、星火決策、回合結算與房主 mutation 成功後，將 room expiry 更新為該次活動後 7 天；GET／polling、被拒絕或失敗的 mutation 不延長期限。
4. Player 活動只延長該 Player session；Host 操作只延長 Host session。session expiry 取「該次活動後 7 天」與 room expiry 的較早者。
5. 房間完成後固定為結局時間後 7 天；後續讀取不延長房間或 session。
6. 三個 browser cookies 的 `Max-Age` 建議統一為 7 天；server-side expiry 才是授權依據，cookie 存在不代表 session 有效。
7. 過期 current-session／current-room 回 `401 SESSION_NOT_FOUND`；過期 mutation 沿用 `HOST_SESSION_REQUIRED` 或 `PLAYER_SESSION_REQUIRED`，不得先洩漏 CSRF／version 等細節。

### Transfer code 與 reassign

1. 房主以 Host session＋CSRF＋room version＋`Idempotency-Key` 為指定 Player 發行 transfer code；同一 Player 新碼會使尚未使用的舊碼失效。
2. API 建議拆為：
   - `POST /rooms/{room_id}/players/{player_id}/transfer-codes`：房主發碼，只在 response 顯示一次。
   - `POST /rooms/{room_id}/players/{player_id}:reassign`：新裝置提交 transfer code 與 room version，成功後取得新的 Player cookie／CSRF。
3. Code 綁定 room＋Player，10 分鐘後失效；server 只保存 code hash、expiry、consumed timestamp 與必要 audit metadata。
4. Redeem 必須原子完成：consume code、rotate Player session／CSRF、保存 room；任何一步失敗都不能留下半完成狀態。
5. 已開始或已滿房仍可轉移既有 Player，因為不新增 roster 成員；完成或過期房間不可再發碼或兌換。
6. 房主轉移自己的 Player 身分時，只撤銷 Player session；獨立 Host session 留在原裝置。Host session 跨裝置轉移不在 MVP。

## Acceptance criteria

1. 未到期的 Host／Player 可恢復並執行既有授權操作。
2. 精確到期邊界、過期後 current read 與 mutation 均被拒絕；重新提交舊 cookie 不會恢復。
3. 只有核准的成功活動會更新 room／actor session expiry。
4. Memory 與 PostgreSQL repository 可完整 round-trip lifecycle／transfer metadata，application restart 後結果一致。
5. 房主可為指定 Player 取得一次性 10 分鐘 code；無 Host、錯 CSRF、舊 version 與 replay 都被拒絕。
6. 正確 code 只成功一次；錯誤、過期、錯 room／player、已用 code 都失敗。
7. 成功 reassign 後，新裝置可繼續遊戲，舊裝置下一次讀取或 polling 得到 `401`。
8. 兩個 concurrent redeems 最多一個成功；Tier 2／多 process 前必須由 PostgreSQL conditional update／transaction 保證，而不是只靠 process memory。

## 不在本切片

- Email／密碼帳號、自助找回、Host session 跨裝置轉移。
- WebSocket、跨分頁同步、永久玩家帳號。
- 房間資料刪除排程；cleanup 另以 PostgreSQL maintenance contract 實作。
- ECS 多 task 部署；在 durable CAS／idempotency 完成前仍維持單 process。

## TDD 與 sensitivity

依序進行：Clock／expiry domain → repository round-trip → authorization → activity allowlist → host 發碼 → atomic redeem／revoke → replay／concurrency／restart → Browser E2E。

至少注入以下錯誤並確認測試會失敗：`>=` 改為 `>`、7 天改 8 天、失敗 mutation 錯誤延長期限、移除 Host／CSRF／version guard、10 分鐘改 11 分鐘、取消 code binding／consume、保留舊 session hash，以及允許兩個 concurrent redeems 同時成功。

## Rollback

每個行為切片可獨立回復 Red／Green commits。不得在只有部分 lifecycle metadata 的狀態部署；migration 必須可重跑，rollback 不得重新啟用已撤銷的 session 或已使用的 transfer code。
