# Deterministic 回合裁定 vertical slice 驗證

- 日期：2026-08-08
- 範圍：本機 FastAPI＋Browser
- AWS 寫入／新增資源／費用：無
- Demo 狀態：暫時驗證用 `8765` 已停止，驗證分頁已關閉

## 完成範圍

- 玩家提交行動時選擇勇氣、洞察或羈絆。
- 收齊所有玩家行動後，房間由 `COLLECTING_ACTIONS` 進入 `AWAITING_HOST`。
- 只有房主 session 可呼叫 `POST /api/v1/rooms/{id}/rounds/{round}:roll`。
- 每位玩家以 `2d6 + 選擇屬性` 計算固定判定：`10+` 成功、`7–9` 部分成功、`6-` 失敗。
- 成功暫存進度 `+2`；部分成功暫存進度 `+1`、危機 `+1`；失敗暫存危機 `+2`。
- 擲骰結果先進入 `AWAITING_SPARK`，進度與危機尚未寫入正式點數，保留下一階段的星火決策空間。
- 行動在收集／等待房主時只顯示提交狀態；擲骰後才向所有玩家揭露文字與結果。
- 擲骰 mutation 檢查 host session、CSRF、room version 與 `Idempotency-Key`。

## 自動測試

- 後端：`16 passed`。
- 前端：`24 passed`。
- 固定骰序列驗證成功、部分成功、失敗三種結果及 `6／7／9／10` 邊界。
- 非房主擲骰回傳 401。
- 相同 idempotency key replay 不重新擲骰、不增加 version。
- 三位玩家結果合計為待結算進度 `+3`、危機 `+3`，正式點數仍為 `0／0`。
- API 不接受前端指定 player ID；行動方式與 owner 分別由 allowlist 與 session 驗證。

## Browser 驗證

1. `http://127.0.0.1:8765/` 由 FastAPI 同源正確載入。
2. 行動表單顯示勇氣、洞察、羈絆三種行動方式。
3. 狀態欄顯示骰點結果區塊與「尚未擲骰」。
4. Demo room 尚未收齊行動時，房主擲骰控制維持隱藏。
5. 未具玩家 session 時，行動文字與屬性輸入維持 disabled。
6. Browser Console errors：0。

## 尚未完成

- 星火是否使用、重擲策略與最終點數套用。
- 回合敘事生成、清除行動、進入下一回合及結局判定。
- 完整三個獨立 Browser player session 的正面擲骰流程由後端整合測試覆蓋。
- Memory repository 不跨 server restart；本證據不是 AWS Tier 0 完成證據。
