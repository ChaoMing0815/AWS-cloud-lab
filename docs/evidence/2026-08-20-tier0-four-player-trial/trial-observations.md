# 四玩家公開試玩情境紀錄

## 環境

- 日期：2026-08-20（Asia/Taipei）。
- 開始：約 22:14；房間刪除的後端精確時間為 22:53:22。
- 房主：受測者 A，iPhone 12／Safari。
- 其他玩家：專題使用者，macOS／Chrome；受測者 C、D，Windows／Chrome。
- 規模：四位玩家、四回合、一次世界草稿與完整結局。

裝置與 Browser 只用於相容性分析，不保存 IP、ISP、帳號或真實身分。

## 情境與結果

### 1. 世界尚未開放前加入

- 房主建立房間並分享房號後，兩位玩家在世界尚未確認／開放前嘗試加入，畫面顯示加入失敗。
- Sanitized access-log 統計為 `rooms:join 409 × 11`、正式開放後 `rooms:join 201 × 3`；最終三位外部玩家均加入成功。
- 判定：伺服器正確拒絕尚未開放的加入，但 UI 應顯示明確原因，並避免玩家無法理解地重複嘗試。

### 2. 世界生成、回合數與同步

- 約 22:18，房主輸入關鍵字與補充資訊並執行一次世界草稿生成，成功得到完整世界設定；CloudWatch 同時間有一次 Nova Lite invocation。
- 世界開放後三位玩家均可加入。Desktop Chrome 大致可自動看到其他玩家動作。
- iPhone 12 Safari 沒有穩定自動刷新新玩家與後續狀態，需要多次手動重新整理。
- 世界草稿生成前，回合上限從預設 `6` 改成其他值後會復原；世界生成後可改為 `4` 並完成遊戲。
- 初步分類：前端 polling／state reconciliation 與 setup form state 問題，不是 AWS service failure。Safari 根因尚未由 browser-level evidence 確認。

### 3. 角色儲存後前端例外

- 四位角色最後都成功儲存並完成遊戲。
- 至少一位玩家在角色儲存後看到原始例外：`Cannot destructure property 'nickname' of 'undefined' as it is undefined.`
- 後端時間窗沒有 `5xx`；route 統計有 `character 200 × 7`、`character 409 × 4`。
- 初步分類：前端在 participant／character mapping 尚未齊備時 destructure `undefined`，且把內部 exception 直接暴露給玩家。需要以 TDD 重現後修正，不能只替換錯誤文字。

### 4. 刪除房間後導頁

- 四回合與結局完成後，房主刪除房間。
- 後端 `DELETE` 於 22:53:22 回 `204`，證明刪除成功。
- 所有裝置均未立即離開原 room route。房主手動重新整理後回首頁；其他玩家手動重新整理後曾顯示不存在房間的 fallback／stale room 畫面。
- `rooms/current 404` 從 22:53:46 開始，到查詢窗 22:59:59 共 317 次，全部發生在成功刪除之後。
- 初步分類：前端刪除事件廣播／polling lifecycle、session invalidation 與 route fallback 問題；不是 RDS 刪除失敗。

### 5. AI 敘事品質

- Nova Lite 能依四位玩家的 action、骰點與進度／危機產生四回合敘事及結局。
- 受測者觀察：輸出較像把玩家行動依序合併成句子，較少演繹行動造成的後續情節。
- 初步分類：Prompt assembly、敘事指令與 context shaping 的 post-MVP 優化；不影響本輪 EC2／RDS／Bedrock 整合通過結論。

## 後續驗證路由

- SSM 只用於限定時段的 sanitized application／access log 查詢，不輸出 client IP、room／player ID、prompt、cookie、token 或 secret。
- 世界開放前加入：若需要精確時間序列，再查 22:14–22:20 的 `rooms:join` status 分布。
- 角色例外：需要受測者提供約略時間後，再查相鄰 `character` request status；由於目前沒有 `5xx`，browser reproduction 與前端測試比重查整段 server log 更重要。
- Safari 同步：SSM 只能證明 server request 是否到達；判定 timer throttling、visibility 或前端 reconciliation 仍需 Safari/browser-level reproduction。
- 刪房導頁：既有 `DELETE 204` 與 post-delete `404` 時序已足夠，不重複查詢。

## 原始截圖處理

本批原圖包含公開 IP、已刪除房號、玩家暱稱、手機通知或 Browser 分頁資訊，暫不直接收入 Git。後續只保存經檢查的裁切／遮罩版本，或以本文件的去識別化文字結論取代：

- iPhone 世界草稿與四回合設定。
- iPhone 房主控制與玩家未同步畫面。
- iPhone 第四回合狀態與骰點。
- 玩家刪除房間後重新整理的 fallback 畫面。
- 角色儲存後 JavaScript exception。
- 四玩家 Round 2 與 AI 敘事畫面。
