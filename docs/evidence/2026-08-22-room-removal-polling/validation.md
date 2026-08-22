# 刪房後舊分頁 polling lifecycle 驗證摘要

- Scope／risk／upstream：R2 可觀察導頁與 polling lifecycle；依 8/20 公開試玩刪房後 `317` 次 `404` finding。
- Baseline：Frontend `88 passed`；工作樹與遠端原先一致。
- Red commit：`a2b192d`。
- Red verification：targeted `1 passed, 1 failed`；失敗精確證明 `ROOM_NOT_FOUND` 仍向外拋出。
- Green commit：`f97a059`。
- Affected verification：polling＋房主刪房 tests `15 passed`。
- Full regression：Frontend `90 passed`。
- Positive：第一個 `404 ROOM_NOT_FOUND` 清除舊 room、停止排程並只導回首頁一次。
- Boundary：其他 `404` 不會被誤判為房間已刪除；`401`／`403`、`409` 與 bounded backoff 維持既有行為。
- Regression guard：房主主動永久刪房既有 stop／navigate 行為仍通過。
- Sensitivity：暫時停用 `ROOM_NOT_FOUND` guard 後 targeted test 如預期失敗；mutation 已還原並重跑全綠。
- Browser／AWS：本 slice 未部署、未呼叫 AWS；實際多分頁 Browser gate 留到下一個 release gate。
- Rollback／residual risk：可回復 `f97a059`；AWS active release 尚未包含本修正。
