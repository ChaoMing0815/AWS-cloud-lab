# Tier 0 四玩家公開試玩 AWS 驗證

## 驗證範圍

- 日期：2026-08-20（Asia/Taipei）。
- 試玩時段：約 22:14–22:53；CloudWatch 查詢範圍為 22:10–23:00。
- 參與者：4 人（專題使用者 1 人、外部試玩者 3 人）。
- 流程：建立原創世界、建立 4 個角色、進行並完成 4 回合、產生結局，最後刪除房間。
- 操作邊界：只使用 AWS Console 與既有 SSM Session 進行唯讀查詢；沒有使用 AWS CLI、修改資源、重啟服務或額外呼叫模型。

## 使用者可見結果

- 四位玩家完成同一房間的 4 回合遊戲，頁面同步、回合結算、AI 敘事與結局均成功。
- 本輪沒有使用真實姓名、個資或機密內容。
- 核心流程完成且後端存取紀錄沒有 `5xx`，但至少一位玩家在角色儲存後看到前端例外：`Cannot destructure property 'nickname' of 'undefined' as it is undefined.`；玩家仍可繼續遊戲。
- Desktop Chrome 大致可自動同步其他玩家動作；iPhone 12 Safari 多次需要手動重新整理才能看到最新玩家／回合狀態。
- 遊戲進行中重新載入可從 private PostgreSQL 讀回 canonical room state。房主刪除房間後，各裝置都沒有立即導回首頁；手動重新整理後，房主回首頁，其他玩家曾進入不存在房間的 fallback／stale 畫面。
- 世界草稿生成前，房主將回合上限改為其他值後會回到預設 `6`；世界草稿生成後可成功改為 `4` 回合並完成遊戲。

## Amazon Bedrock

CloudWatch `amazon.nova-lite-v1:0`、Statistic `Sum`、Period `1 minute`：

| 本地時間 | Invocations | InputTokenCount | OutputTokenCount |
| --- | ---: | ---: | ---: |
| 22:18 | 1 | 322 | 520 |
| 22:35 | 1 | 660 | 237 |
| 22:42 | 1 | 649 | 218 |
| 22:47 | 1 | 654 | 238 |
| 22:51 | 2 | 733 | 336 |
| **合計** | **6** | **3,018** | **1,549** |

- 六次 invocation 與一個世界草稿、四個回合敘事及最終結局的預期生成次數一致。
- `InvocationLatency` 使用 `Average`、Period `1 minute`：3,237、1,863、1,784、1,661、1,546 ms；22:51 的資料點包含兩次呼叫，六次呼叫的加權平均約 1,940 ms。
- 應用存取紀錄顯示 `world:generate 200` 一次、`rounds/{round}:resolve 200` 四次；三次重複／衝突 resolve 得到 `409`，未形成額外模型 invocation。

## EC2、RDS 與 HTTP

- EC2 `CPUUtilization` 使用 `Average`、Period `5 minutes`；試玩期間峰值約 `1.8133%`，未觀察到 CPU 壓力。
- RDS `DatabaseConnections` 使用 `Average`、Period `1 minute`；22:26 與 22:44 均觀察到 1 個 client network connection。此 metric 不是逐請求計數，需與 refresh persistence、private RDS 架構及 API 成功紀錄合併判讀。
- HTTP 狀態分布：`200 × 2,671`、`201 × 5`、`204 × 1`、`404 × 317`、`409 × 30`，沒有 `5xx`。
- 核心成功路徑包含房間建立／加入、世界確認、遊戲開始、角色儲存、action、擲骰、星火決策、四次回合結算及房間刪除。
- 房間於 22:53:22 刪除；`rooms/current 404` 首次出現在 22:53:46，最後出現在查詢窗結束的 22:59:59。317 次 `404` 因此是已開啟分頁在房間刪除後繼續輪詢，不是遊戲、EC2 或 RDS 故障。
- `rooms:join 409 × 11` 與受測者在世界尚未開放前重複嘗試加入的紀錄一致；正式開放後有三次 `201`，三位外部玩家均成功加入。
- 其他 `409` 代表重複或不符合當前 canonical state 的操作被拒絕；試玩仍完成且沒有重複結算或狀態損毀。

## 證據索引

- `bedrock-invocations.png`
- `bedrock-input-token-count.png`
- `bedrock-output-token-count.png`
- `bedrock-invocation-latency.png`
- `ec2-cpu-utilization.png`
- `rds-database-connections.png`
- `http-status-distribution.png`
- `sanitized-route-counts.png`
- `sanitized-api-route-counts.png`
- `post-delete-current-404-window.png`

## 結論與限制

- 本輪以 **PASS with findings** 通過 Tier 0 四玩家 AWS 外部 E2E：public HTTPS EC2 Web/API、private RDS persistence 與 Amazon Bedrock 真實生成共同運作，且四位玩家完成四回合與結局。
- CloudWatch metric 與 sanitized access-log 統計能證明服務活動與結果一致，但不是分散式 trace；目前不宣稱每個前端事件都具備跨服務 request-level correlation。
- `rooms/current` 在房間刪除後仍輪詢，造成不必要的 `404` 與請求量；刪除成功但前端未立即導頁，列為前端 session／room lifecycle 缺陷。
- iPhone Safari 需要頻繁手動重新整理，尚不能宣稱 mobile real-time sync 與 Desktop Chrome 等價。
- 角色儲存後的原始 JavaScript exception 直接顯示給玩家，不符合公開錯誤訊息的安全與可理解性目標；需由前端修正為穩定 state mapping 與安全錯誤文案。
- LLM 回合敘事能整合四位玩家行動並維持世界、進度與危機，但受測者認為它偏向逐句摘要，較少根據行動演繹後續劇情；此為 Prompt 組裝／敘事品質優化，不阻斷 Tier 0 AWS 架構驗收。
- EC2 截圖只顯示部分 Instance ID 片段，未包含完整識別碼、account ID、IP、endpoint 或 secret；依專題使用者判定保留。
