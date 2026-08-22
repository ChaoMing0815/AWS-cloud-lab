# Tier 0 公開試玩操作與外部 E2E 驗證指南

- 適用版本：AWS Tier 0 公開 HTTPS 試玩
- 驗證目的：證明外部玩家可透過公開 Web 使用部署於 AWS 的多人遊戲，且 EC2、private RDS、Amazon Bedrock 與持久化流程正常串接
- 建議規模：1 位房主＋2 位玩家，使用三個獨立瀏覽器或裝置
- 驗證範圍：一個房間、一個完整回合、一次 Bedrock 回合敘事與一次重新整理
- 不在範圍：非阻斷性的視覺偏好、一般 UI／UX 滿意度、功能建議與 Prompt Injection 測試
- 隱私原則：使用暱稱，不輸入真實姓名、Email、電話、公司機密或其他個人資料

公開 HTTPS 網址由專題負責人私下傳送，不寫入 GitHub、問卷或公開文件。房主只在受測者之間分享當次房號。受測者不操作 AWS Console，也不接觸任何 credential、cookie、token 或內部 endpoint。

## 角色分工

- 專題負責人：確認 AWS health／cost、提供網址、控制 Bedrock 呼叫上限、保存去識別化證據並在異常時停止測試。
- 房主：建立房間、設定世界、開始遊戲、擲骰與結算回合。
- 兩位玩家：以房號加入、建立角色、提交行動與完成星火決策。

## 試玩前檢查

1. 專題負責人確認 Budget／credits 無告警，EC2 application 與 public Nginx 正常。
2. 三位受測者使用不同瀏覽器、無痕視窗或裝置；記錄 Browser 名稱、大版本與 Desktop／Mobile，不記錄 IP。
3. 記錄測試開始時間與時區，供 Bedrock metrics、application logs 與 Cost Explorer 對照。
4. 三位受測者確認網頁可開啟、沒有 certificate warning，且頁尾顯示 `AWS Tier 0 公開試玩`。
5. 每位受測者使用不含真實身分的暱稱。
6. 房主手動輸入世界，避免將世界草稿生成額度混入多人 E2E；本次只允許房主結算時的一次 Bedrock 回合敘事。
7. 不進行 Prompt Injection、個資或有害內容測試；安全代表性測試已由 Batch 7、9C、9D 分開完成。

## 三玩家一回合流程

1. 房主建立房間，完成世界設定並私下分享六碼房號。
2. 兩位玩家從首頁加入；三個畫面都應顯示 `3 / 5`。
3. 三位玩家分別建立角色並儲存；Lobby 應顯示 `3 / 3` 角色完成。
4. 房主開始遊戲；三位玩家各自提交一項行動。
5. 三個畫面都應顯示 `3 / 3` 已提交，且其他玩家在結算前看不到彼此的行動內容。
6. 房主擲骰；三位玩家分別決定使用或保留星火。
7. 房主結算回合；只允許一次 Bedrock 回合敘事，不因文案偏好重試。
8. 三個畫面應同步進入下一回合，並顯示相同的 Round、進度、危機與故事敘述。
9. 每位玩家重新整理一次；session、角色、Round、進度、危機與故事狀態都應保留。
10. 記錄完成時間、是否成功與任何停止階段；不繼續第二回合。

若任何一步失敗，先記錄階段與安全錯誤訊息後停止，不重複點擊可能觸發模型或 mutation 的按鈕。

## 受測者客觀驗證項目

每位受測者只回答 `是`／`否`；若為否，補充失敗階段與畫面上的安全錯誤訊息：

1. 公開 HTTPS 網頁可開啟，且沒有 certificate warning。
2. 可以使用房號加入同一房間。
3. 可以建立角色並完成配點。
4. 可以提交行動並完成星火決策。
5. 三個畫面顯示相同的玩家數、提交數與回合狀態。
6. 房主結算後，三個畫面都出現相同的 AI 故事、進度與危機。
7. 重新整理後仍回到相同房間，角色、回合與故事均保留。
8. 全程沒有 certificate warning、stack trace、AWS 原始錯誤、重複扣除、重複擲骰或重複結算。

另記錄：

- 測試開始／結束時間與時區。
- 完成一回合所需時間。
- Browser 名稱、大版本與 Desktop／Mobile。
- 家用網路或行動網路；不記錄 ISP、IP 或精確位置。
- 任何阻止 E2E 完成的操作問題；非阻斷性的視覺與 UI／UX 意見不納入本輪。

## 專題負責人 AWS 佐證

外部試玩證明使用者旅程可用；下列 AWS 證據由專題負責人另行保存，不要求受測者操作：

- EC2 `Running`、status checks passed、SSM managed node `Online`。
- 公開 HTTPS readiness `200`，HTTP 可正確導向 HTTPS。
- RDS `Available`、`Public access = No`、DB Security Group 的 PostgreSQL `5432` 來源為 App Security Group。
- 既有 application service restart 後仍能由 PostgreSQL 讀回 room／session 的持久化證據。
- 試玩時間範圍內 Nova Lite 的 `Invocations`、`InputTokenCount`、`OutputTokenCount` 與 `InvocationLatency`。
- application log 沒有未處理 `5xx`、stack trace、prompt、room／player identifier、ARN、secret 或 credential。
- 試玩後 Budget、Cost Explorer service breakdown 與 credits 狀態；註明帳務資料可能延遲。

## 停止條件

出現下列任一情況時結束當次試玩，不自行重試模型：

- Certificate warning、無法建立可信任 HTTPS 或公開頁面無法載入。
- 多位玩家持續看到不同 canonical state。
- 同一操作重複扣除次數、重複擲骰、重複結算或回合被推進兩次。
- 公開頁面顯示 stack trace、AWS 原始錯誤、ARN、secret 或其他敏感資訊。
- AI 回覆出現個資、有害內容、未授權規則變更或明顯偏離既定世界。
- Bedrock 呼叫超過本次一次回合敘事的上限。
- Budget／credits 告警或 AWS service health 異常。

## 報告證據

- 保存公開 HTTPS 首頁、三玩家／角色完成、`3 / 3` 行動、骰點／星火、回合結算、Round 2 與 refresh persistence 的去識別化畫面。
- 將受測者結果彙整為完成率、完成時間、失敗階段、Browser／裝置類型與錯誤數，不保存受測者身分。
- 活動中的房號先遮罩；只有房間已刪除或到期、代碼不再可用時，才可保留房號作為隨機代碼設計證據。
- 截圖不可包含 public IP、account ID、ARN、resource ID、Email、cookie、token、真實姓名或未經檢查的自由輸入。
- Browser 成功畫面必須和 EC2／SSM、private RDS、Bedrock metrics、restart persistence、Budget／Cost evidence 配對；Browser 截圖本身不宣稱能單獨證明特定 AWS 服務。

## 驗證摘要模板

```text
日期與時區：
AWS Region：ap-northeast-1
Release：tier0-...
受測規模：1 房主＋2 玩家／3 個獨立 Browser
測試開始／結束時間：
完成時間：
公開 HTTPS：PASS／FAIL
Certificate warning：0／其他
同房加入：3/3／其他
角色完成：3/3／其他
行動提交：3/3／其他
Bedrock 回合敘事：PASS／FAIL
三端 canonical state 一致：PASS／FAIL
Refresh persistence：PASS／FAIL
未處理錯誤：0／其他
重複 mutation：0／其他
停止條件觸發：否／是，原因：
```
