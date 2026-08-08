# Session／CSRF／Idempotency vertical slice 驗證

- 日期：2026-08-08
- 範圍：本機 FastAPI＋Browser
- AWS 寫入／資源／費用：無
- Secret／credential：未建立、未保存

## 自動測試

後端：`10 passed`。

- Create room 產生 host session cookie。
- Join room 產生 player session 與 CSRF context。
- 缺少 `Idempotency-Key` 回傳 400。
- 相同 key／payload replay 不新增第二位玩家。
- 相同 key／不同 payload 回傳 422。
- 無 player session 的 action 回傳 401。
- 缺少 CSRF 的 action 回傳 403。
- 正確 player session＋CSRF 可提交。
- 其他 player view 只看到 `hasSubmitted`，看不到 action text。
- Room version conflict 維持 structured 409。

前端：`15 passed`。

- Mutation 送出 `Idempotency-Key`。
- Action 使用 session response 的 `X-CSRF-Token`。
- Action body 不再包含前端指定的 `player_id`。
- 既有 Domain、use case、Mock／Fetch adapters tests 均通過。

## Browser 正面驗證

1. 匿名頁面顯示 3 位 demo 玩家，但 action textarea／player select 都 disabled。
2. 加入「安全測試玩家／謹慎的觀察者」後顯示 `4 / 5`。
3. Player select 只包含目前 session 對應的單一角色。
4. 提交「我先確認封條附近是否有人看守。」成功，顯示 `1 / 4` 與「已提交」。
5. 未結算前 story feed 不含 action text。
6. Refresh 後 session、單一角色選項與 `1 / 4` 提交狀態恢復。
7. Browser Console errors：0。

## 限制

- Cookie `Secure=False` 僅供 localhost HTTP；AWS HTTPS 必須改為 `Secure=True`。
- Host session 已簽發與辨識，但尚未有 host-only mutation endpoint。
- Memory idempotency records 與 session hashes 不跨 server restart。
- 本證據不是 AWS Tier 0 完成證據。
