# 2026-08-09 星火與完整單回合驗證

## 驗證範圍

本階段只完成本機 vertical slice，不操作 AWS、不串接真實 LLM、不建立計費資源。驗證流程如下：

```text
三位玩家提交行動
  → 房主擲骰
  → 玩家 USE／DECLINE 星火
  → 房主結算或明確略過等待者
  → 套用正式進度／危機與星火
  → MockStoryteller 新增敘事
  → 清除行動並進入下一回合
```

## 自動測試結果

| 範圍 | 結果 | 主要證據 |
| --- | --- | --- |
| 後端 | `18 passed` | 6→7、9→10、三種判定、三玩家完整回合、無星火、CSRF、非房主、pending gate、房主略過、replay |
| 前端 | `28 passed` | use cases、Fetch adapter 的 player／host CSRF 邊界、Mock adapter 完整回合 |

唯一警告為 FastAPI TestClient 使用的 Starlette／httpx 相容性 deprecation；不影響本次測試結果，後續更新依賴時處理。

## 狀態與副作用驗證

- `AWAITING_SPARK` 只接受目前 player session 的星火決策。
- `USE` 將最終總值加 1 並重新分類結果；`DECLINE` 不改變結果。
- 無星火時 `USE` 回傳 conflict，不會讓星火低於 0。
- 尚有等待者且 `skip_pending_spark=false` 時拒絕結算。
- 房主明確設定略過後，等待者視為 `DECLINE`。
- 非房主不能結算；錯誤 CSRF 被拒絕。
- 結算後才套用正式進度／危機、扣除已使用星火；失敗補 1 星火且上限為 3。
- 相同結算 idempotency key replay 不會重複加點、扣星火、新增故事或推進回合。
- `MockStoryteller` 只產生 narrator entry，不修改規則狀態。

## Browser smoke test

- 暫時以 `http://127.0.0.1:8765/` 載入 FastAPI 同源頁面。
- FastAPI 模式、正式進度／危機區塊、玩家星火控制與房主結算控制皆存在。
- 畫面無明顯溢位或破版。
- Browser Console：`0 errors`。
- 驗證完成後已關閉分頁並停止 8765 伺服器。

## 尚未完成

- 4／6／8 回合上限、100% 提前完成與結局頁。
- 三個獨立瀏覽器工作階段的人工 E2E；本次三玩家流程由 FastAPI integration test 覆蓋。
- PostgreSQL、server restart 後持久化與 production session lifecycle。
- 真實 Bedrock／LLM adapter、retry、schema validation 與 fallback。

## 成本與安全

- 未登入或操作 AWS Console／CLI。
- 未建立或修改任何 AWS 資源，AWS 費用影響為 `US$0`。
- 未新增 API key、Access Key、Email、account ID 或 session token 至 repository。
