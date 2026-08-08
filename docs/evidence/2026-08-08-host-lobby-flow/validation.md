# Host 世界設定與 Lobby start vertical slice 驗證

- 日期：2026-08-08
- 範圍：本機 FastAPI＋Browser
- AWS 寫入／新增資源／費用：無
- Credential／Access Key：未建立、未保存

## 實作範圍

- 新房間建立為 `DRAFT`。
- 房主直接輸入故事名稱、背景、目標、初始場景、核心阻礙、調性與 4／6／8 回合上限。
- 房主確認世界後進入 `LOBBY`，此時才允許玩家加入。
- 3–5 位玩家時，房主可以開始並進入 `COLLECTING_ACTIONS`。
- 世界確認與開始遊戲均檢查 host session、host CSRF、room version 與 `Idempotency-Key`。
- Room code 不構成房主授權。

## 自動測試

後端：`13 passed`。

- 世界確認缺少 host session 回傳 401。
- 有 host session 但缺少 CSRF 回傳 403。
- 合法世界確認進入 `LOBBY` 並鎖定回合上限。
- `DRAFT` 房間拒絕玩家加入。
- 人數不足拒絕開始。
- Player session 不能代替 Host session 開始遊戲。
- 三位玩家後合法開始，保存 `initialPlayerCount=3` 並揭露初始場景。
- 既有 version、idempotency、action session 與 action privacy 測試維持通過。

前端：`19 passed`。

- `ConfirmWorld` 正規化輸入並驗證回合上限。
- `StartGame` 只透過 `GameApi` port。
- `FetchGameApi` host mutation 傳送 host CSRF 與 `Idempotency-Key`。
- `MockGameApi` 與 HTTP adapter 維持相同狀態機契約。

## Browser 驗證

1. 建立房間後顯示 `DRAFT` 世界表單，玩家加入與 action 均不可用。
2. 填寫完整世界並確認後，畫面進入 Lobby、顯示 room code、世界與共同目標。
3. 0 位玩家時開始按鈕 disabled，提示至少還需 3 位玩家。
4. 房主加入自己成為玩家後，host 控制仍保留；1 位玩家時開始按鈕仍 disabled。
5. Player action 在開始遊戲前維持 disabled。
6. Browser Console errors：0。

初次 Browser 驗證發現 busy cleanup 會在 render 後重新啟用「開始遊戲」按鈕。後端仍會拒絕人數不足請求；前端已修正並重新載入驗證 disabled 狀態。

## 尚未完成

- 角色完整欄位與屬性配點尚未實作；目前加入時的角色描述仍是暫時欄位。
- 世界關鍵字／LLM 草稿生成尚未實作；目前為直接輸入模式。
- Browser 正面開始流程由後端三玩家整合測試覆蓋；單一 in-app browser session 不模擬三個獨立 player cookies。
- Session expiry／revoke／reassign 與 production `Secure=True` cookie 尚待後續階段。
- Memory repository 不跨 server restart；本證據不是 AWS Tier 0 完成證據。
