# 共演計劃 Screen States

- 狀態：Active target
- Owner：Product／UX
- Source of Truth：是，僅負責使用者可見狀態
- Depends on：[Web App User Flow](user-flow.md)、[正式 MVP Spec](../specs/text-rpg-mvp-spec.md)
- 最後檢視：2026-08-09

> 各狀態的後端授權與遊戲規則仍引用正式 MVP Spec；本表避免在每個 Feature Spec 重複定義共通 UX。

## 共通狀態

| 狀態 | 使用者可見行為 | 禁止行為 |
| --- | --- | --- |
| Loading | 顯示目前載入項目，保留既有安全畫面 | 不顯示 Demo 假資料冒充正式資料 |
| Submitting | 送出按鈕停用並顯示進度 | 不重複 mutation |
| Validation error | 欄位附近顯示可修正原因，focus 第一個錯誤 | 不清空其他合法輸入 |
| Offline | 保留最後已確認資料，顯示離線與重連狀態 | 不把未確認 mutation 宣稱成功 |
| Session expired | 說明身份已過期並提供回首頁或角色轉移下一步 | 不無限重試 `401/403` |
| Version conflict | 重新載入 canonical state，再說明資料已更新 | 不以舊 version 覆寫 |
| Unexpected error | 顯示 request ID 與可執行下一步 | 不顯示 stack、SQL、AWS 原始錯誤或 secret |

## 各頁狀態

| 頁面 | Empty／Idle | Loading／Submitting | Error／Recovery | Success／Exit |
| --- | --- | --- | --- | --- |
| `/` 首頁 | 建立、加入、Demo；有效 session 才顯示繼續 | 檢查 session 時顯示短暫載入 | Session 指向不存在房間時清除 pointer 並說明 | 進入 setup、lobby、play、ending 或 demo |
| 建立遊戲 | 暱稱空白 | 建立房間中 | 暱稱格式、伺服器錯誤 | 建立 Host＋Player 身份並進入 setup |
| 加入遊戲 | room code、暱稱空白 | 驗證並加入中 | 格式錯誤、不存在、已滿、已開始、暱稱重複 | 建立 Player session 並進入 lobby |
| 世界設定 | 手動表單或關鍵字模式 | LLM 草稿生成中／確認中 | 生成限制、內容拒絕、timeout；保留輸入 | 確認世界並進入 lobby |
| Lobby | 玩家列表、角色未完成 | 輪詢、儲存角色、開始遊戲 | 人數不足、角色未完成、session／version conflict | 進入 play |
| Play | 依房間狀態顯示等待或操作 | 提交、擲骰、星火、結算、polling | Offline、權限、衝突、`RESOLUTION_FAILED` | 下一回合或 ending |
| LLM 復原 | 顯示已鎖定判定與失敗原因分類 | 自動／手動重試 | 再次失敗仍可 fallback | 故事提交，不改 canonical rules |
| Ending | 顯示結局、進度、危機與故事 | 刪除房間中 | 刪除失敗保留畫面 | 回首頁或確認資料已刪除 |
| `/demo` | 固定教學場景 | 僅本機 Mock 狀態轉換 | 可重設 Demo | 結束後回正式首頁 |

## Polling UX

- 正常間隔 3 秒；同一時間只能有一個 request。
- 暫時失敗採 3、5、10 秒 bounded backoff；成功後恢復 3 秒。
- 離開同步頁、切換房間、結局完成時取消 polling。
- `401/403` 停止輪詢並顯示 session 狀態；`409` 先重新載入；暫時性 `5xx`／網路錯誤保留畫面並重試。

## 最低 Accessibility

- 所有 input 有可見 label，錯誤可由 assistive technology 讀取。
- Modal／確認流程管理 focus，鍵盤可完成主要流程。
- 不只以顏色表示玩家、連線、成功或錯誤狀態。
- Desktop 為 Demo 主要目標；窄螢幕仍須可閱讀且不能產生主要操作水平溢出。
