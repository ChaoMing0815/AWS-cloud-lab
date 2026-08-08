# 前端 Clean Architecture vertical slice 驗證

- 日期：2026-08-08
- 範圍：本機前端
- AWS 寫入：無
- AWS 費用：無

## 自動測試

執行方式：

```bash
cd web
npm test
```

結果：

- Tests：9
- Passed：9
- Failed：0
- 涵蓋 nickname／role validation、create／join use cases、六碼 room code、room version、重複 nickname、五人上限與 immutable snapshot。

## 瀏覽器 smoke test

本機網址：`http://127.0.0.1:8080/`

正面流程：

1. 頁面成功載入 `本機 Mock API 模式`，初始展示為三位玩家。
2. 點擊「建立新房間」。
3. 顯示新的六碼 room code、`0 / 5` 與「已建立新的 Mock 房間」。
4. 無玩家時 action textarea 為 disabled。
5. 輸入「測試玩家」與「細心的企劃」，提交加入。
6. 顯示 `1 / 5`、玩家名稱／角色與「玩家已加入房間」。
7. 玩家加入後 action textarea 正確解鎖。
8. Browser Console errors：0。

## 靜態邊界

- 遊戲 canonical state 不再寫入 `localStorage`。
- 前端原始碼沒有 `fetch` 或 AWS SDK；目前只注入 `MockGameApi`。
- 玩家與故事文字以 DOM `textContent` 建立，不以 untrusted `innerHTML` 渲染。
- 後續 `fetch` 只能加入 `FetchGameApi` adapter。

## 未完成範圍

- 尚未建立 FastAPI／`FetchGameApi`。
- 尚未實作正式 world、character、dice、spark、progress、danger 與 LLM resolution。
- Mock state 只保存在記憶體，重新整理會回到預設展示資料。
- 本驗證不能視為 AWS Tier 0 完成證據。
