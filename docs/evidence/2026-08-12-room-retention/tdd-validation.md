# 到期房間清理 TDD 驗證紀錄

日期：2026-08-12  
範圍：到期房間 retention cleanup use case 與 Memory／PostgreSQL repository bulk delete。

## Red

1. 指令：`../.venv/bin/pytest -q tests/test_room_retention_cleanup.py`
2. 結果：3 failed，皆為預期的「cleanup use case 尚未建立」assertion。
3. Red checkpoint：`74136c1 test(red): specify expired room retention cleanup`。

## Green

1. UTC-aware `now` 下，所有狀態的 `expires_at <= now` 房間均刪除；未到期與 `None` demo 房保留。
2. 同一 cleanup 可重跑；第二次回傳 0。
3. Memory adapter 在 lock 內刪除；PostgreSQL adapter 使用單一參數化 `DELETE`，不載入 aggregate。
4. 目標測試：3 passed；全後端回歸：224 passed、8 skipped。

## 故障注入

1. 刻意將 Memory 邊界從 `<= now` 改成 `< now`。
2. 精確到期測試失敗：實際刪除 2，預期 4。
3. 已還原正確邊界並重跑目標測試：3 passed。

本切片不由 Web boot 觸發，未呼叫 AWS 或真實資料庫。
