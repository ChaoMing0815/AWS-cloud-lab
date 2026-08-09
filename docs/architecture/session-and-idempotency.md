# 共演計劃：Session、CSRF 與 Idempotency 設計

- 狀態：本機 memory vertical slice 已實作
- 日期：2026-08-08
- 補充決策日期：2026-08-09
- AWS 寫入／費用：無

## 安全目標

- 房主與玩家使用不同 opaque session，不以 room code 代表授權。
- 瀏覽器 JavaScript 無法讀取 session token。
- 後端只保存 session token 的 SHA-256 hash，不保存 cookie 明文。
- Action 的 player 身分由後端 session 決定，前端不得指定任意 `player_id`。
- 已認證 mutation 同時檢查 CSRF、room version 與 idempotency key。
- Action 鎖定前，其他玩家只能看到是否提交，不能看到文字。

OWASP 建議自訂 session ID 使用 CSPRNG、至少 128 bits，且不要把 session token 放進 `localStorage`；cookie 應使用 `HttpOnly`、`Secure` 與 `SameSite` 等屬性。[OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

## Cookie 與伺服器資料

| Cookie | 用途 | JavaScript 可讀 | 本機屬性 |
| --- | --- | --- | --- |
| `co_story_host` | 房主 opaque session | 否 | `HttpOnly; SameSite=Lax` |
| `co_story_player` | 玩家 opaque session | 否 | `HttpOnly; SameSite=Lax` |
| `co_story_local_room` | 本機 current room pointer，不是授權 | 否 | `HttpOnly; SameSite=Lax` |

Session token 由 server-only 隨機 HMAC secret 與本次 idempotency key 導出 256-bit opaque value；Room／Player 只保存 token hash。CSRF token 與 session 綁定，由 API response 的 `session.csrfToken` 提供給同源 JavaScript，僅保存於記憶體。

本機 HTTP 必須使用 `Secure=False` 才能測試；部署至 HTTPS 時必須改成 `Secure=True`，並評估 `__Host-` cookie prefix、有效期限、撤銷與 server-side expiry。

## CSRF

玩家 action mutation 需要：

```text
Cookie: co_story_player=<opaque token>
X-CSRF-Token: <session-bound token>
```

後端先以 cookie hash 找到 Player，再以 constant-time comparison 驗證 CSRF token。缺少／錯誤 token 回傳 `403 CSRF_FAILED`；只有 CSRF token、沒有 player session 時回傳 `401 PLAYER_SESSION_REQUIRED`。

OWASP 建議 stateful 應用使用 synchronizer token，並以 custom request header 傳送；custom header 也會受到瀏覽器 same-origin policy 約束。`SameSite` 是額外防線，不單獨取代 CSRF token。[OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)

目前 create room／join room 是匿名 bootstrap mutation，不使用既有授權 cookie，因此要求 `Idempotency-Key`，但不要求 CSRF。Host-only world／start／roll／resolve／finish 已使用 host session 與 host CSRF token。

目標正式入口會把建房改為原子性建立 Host session、房主的 Player 與 Player session；房主是 3–5 位玩家之一。跨裝置取回既有角色時，由房主產生有效 10 分鐘的一次性轉移碼，成功後撤銷舊 Player session。完整核准內容見[產品核准紀錄](../governance/approval-log.md)。

## Idempotency

目前所有 create／join／action mutation 都要求：

```text
Idempotency-Key: <client-generated UUID>
```

伺服器以 `operation scope + key` 保存 payload fingerprint 與原始結果：

- 缺少 key：`400 IDEMPOTENCY_KEY_REQUIRED`。
- 同一 key＋同一 payload：回傳第一次結果，不重複 mutation。
- 同一 key＋不同 payload：`422 IDEMPOTENCY_KEY_REUSED`。
- Key scope 包含 operation、room、round 與 player，避免不同操作互相碰撞。

`Idempotency-Key` HTTP header 仍是 IETF work-in-progress draft；本專題採用其「唯一 key、不得重用於不同 payload、缺少 key 與 payload conflict 應明確失敗」語意，但不將草案視為已發布 RFC。[IETF Idempotency-Key draft](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header)

目前 store 位於 memory，server restart 後紀錄消失。切換 PostgreSQL 時必須建立 unique constraint、payload fingerprint、response snapshot 與 expiry，並讓相同 scope／key 的 concurrent request 只有一個 operation 可以 commit。

## Action 隱私

- Request body 只包含 `text` 與 `room_version`，不接受 `player_id`。
- 後端由 `co_story_player` 找出 action owner。
- 回合未結算時，其他玩家只收到 `hasSubmitted=true`，`action=""`。
- 當前玩家可以在自己的 player view 看到自己的 action。
- Action story entries 只在 round 推進後才加入公開 response。

## 尚未完成

- Session server-side expiry、revoke、reassign 與 logout。
- Production HTTPS `Secure` cookie 與 reverse proxy trusted headers。
- Origin／Fetch Metadata defense-in-depth policy。
- PostgreSQL session／idempotency persistence 與 concurrent transaction test。
- 正式跨裝置 reassign 與舊 session 失效測試。
