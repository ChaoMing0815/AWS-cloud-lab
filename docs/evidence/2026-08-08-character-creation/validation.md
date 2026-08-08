# 角色建立與三點配點 vertical slice 驗證

- 日期：2026-08-08
- 範圍：本機 FastAPI＋Browser
- AWS 寫入／新增資源／費用：無
- Demo 狀態：`8000` 與暫時驗證用 `8765` 均已停止

## 完成範圍

- 角色名稱、背景、特質與弱點。
- 勇氣、洞察、羈絆各為 0–2，總和必須等於 3。
- 星火由後端固定建立為 1，不接受前端指定。
- 玩家只能透過自己的 opaque session 建立或更新自己的角色。
- Character mutation 檢查 player CSRF、room version 與 `Idempotency-Key`。
- 只有 `LOBBY` 可以編輯角色。
- 3–5 位玩家必須全數完成角色，房主才能開始遊戲。

## 自動測試

- 後端：`14 passed`。
- 前端：`22 passed`。
- 無 Player session 的角色 mutation 回傳 401。
- 非法 `2/2/0` 配點回傳 422；合法 `2/1/0` 成功。
- 相同 idempotency key replay 不重複增加 version。
- Player ID 不由前端傳送，角色 owner 由 session 決定。
- `CHARACTERS_INCOMPLETE` 阻擋未完成角色的 start。

## Browser 驗證

1. 建立房間並確認世界後進入 Lobby。
2. 玩家加入後顯示完整角色表單與預設 `1/1/1`。
3. 角色未儲存前顯示「角色未完成」，開始按鈕 disabled。
4. 改為 `2/1/0` 時顯示「配點完成」。
5. 儲存後 roster 顯示角色名稱與「角色已完成」。
6. 房主狀態顯示 `1/1` 位完成角色，但因玩家不足仍不能開始。
7. Action 在 Lobby 階段維持 disabled。
8. Browser Console errors：0。

## 尚未完成

- 完整三個獨立 Browser player session 的正面開始流程由後端整合測試覆蓋。
- Action approach、骰子、星火決策、進度、危機與結局尚未實作。
- Memory repository 不跨 server restart；本證據不是 AWS Tier 0 完成證據。
