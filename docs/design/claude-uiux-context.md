# 共演計劃：Claude UI／UX 設計 Briefing

- 文件用途：提供 Claude 一次完成 UI／UX review 所需的產品、現況與限制。
- 程式事實基準：Production source exact SHA 為 `372a2cb77c85530b9cb3bedbd39de9d4b88e535a`；UI 文案方向另以尚未部署的整理 commit `0943f08` 為準（2026-09-01 檢視）。本文件是設計交接資料，不是 deployment evidence。
- 交付期待：請提出小規模、可分階段落地的建議；不要直接改程式、重新定義遊戲規則或擴張 Support Agent 能力。
- 事實來源：[正式 MVP Spec](../specs/text-rpg-mvp-spec.md)、[Web App User Flow](../product/user-flow.md)、[Screen States](../product/screen-states.md)、[目前交接](../handoffs/CURRENT.md)、[入口 Feature](../features/entry-and-room-join.md)、[Polling Feature](../features/polling-offline-reconnect.md)、[Tier 2 async flow](../features/tier2-async-flow.md)、[Support Agent integration](../features/support-agent-integration.md)、[前端 ADR](../decisions/0002-adopt-clean-frontend-architecture.md) 與 [Support Agent ADR](../decisions/0005-adopt-bounded-support-agent-core.md)。

## 1. 產品與玩家目標

「共演計劃」是 3–5 人、4／6／8 回合、純文字的多人 AI 共創故事遊戲。房主也是玩家；大家在同一世界建立自由角色、秘密提交行動，再由後端公開規則決定骰點、星火、進度與危機。AI 故事主持人只把已確定的結果整理成連貫原創敘事，不能改規則或 canonical state。

玩家的核心目標是：低門檻地與朋友開始一局、清楚知道現在輪到誰做什麼、理解自己的選擇造成何種後果，並在短暫離線或 AI 延遲時仍相信遊戲狀態沒有遺失。

房主除了一般玩家操作，另負責世界設定、開始遊戲、擲骰／結算、處理離線玩家與故事生成失敗，以及在結局後永久刪除房間。介面必須清楚區分「所有玩家可做」「目前玩家可做」與「僅房主可做」。

## 2. 主要頁面、流程與狀態

目前是單一 HTML app shell，由輕量 router 顯示對應區塊：

| 頁面／路徑 | 主要目的 | 重要狀態 |
| --- | --- | --- |
| `/` 首頁 | 建立房間、以六碼房號加入、有效 session 時繼續遊戲；Demo 是次要入口 | 載入 session、提交中、輸入錯誤、可繼續／無 session |
| `/rules` | 靜態快速規則 | 五段新手規則與返回首頁 |
| `/support` | 匿名規則查詢；有 Player session 才能建立問題草稿 | capability disabled、查詢中、supported／unsupported、草稿成功、安全錯誤／rate limit |
| `/host/setup` | 房主手動填寫或以 3–5 個關鍵字生成可編輯世界草稿 | `DRAFT`、生成中、欄位錯誤、最多兩次生成、確認世界 |
| `/room/:code/lobby` | 分享房號、3–5 人加入、各自建立角色、全員完成後由房主開始 | 人數不足、角色未完成／完成、房主 start gate |
| `/room/:code/play` | 閱讀共同故事、提交行動、擲骰、星火、非同步結算、進度／危機 | `COLLECTING_ACTIONS`、`AWAITING_HOST`、`AWAITING_SPARK`、`RESOLVING`、`RESOLUTION_FAILED`、`COMPLETION_AVAILABLE` |
| `/room/:code/ending` | 顯示最終故事、結果與代價；房主可永久刪除 | `COMPLETED`、刪除確認／失敗／完成 |
| `/demo` | 第一次使用者的固定單人教學 | Mock-only、不呼叫正式 API、不建立 session、不保存進度 |

遊戲頁在桌面是三欄：左側房間／世界／玩家與設定，中間故事 feed 與行動 composer，右側回合狀態／進度／骰點與房主控制。頁面每 3 秒讀取 canonical Room；網路失敗採 3、5、10 秒 bounded backoff並保留最後成功畫面。`401/403` 停止 polling，`409` 重新載入 canonical state。房主送出非同步結算後先看到處理中狀態；60 秒後只提示延遲，不取消、不重送、不自動 fallback。

## 3. 目前視覺語言

- 整體是深色、帶敘事感的「夜色劇場／控制台」：近黑藍綠背景、低透明面板、細框、blur、微弱網格與環境光暈。
- 主色為金色 `#e3b66b`（敘事、主要行動、目標）、青綠 `#63cbb7`（連線、成功、同步）與珊瑚紅 `#e27b6c`（錯誤／危險）。大多數次要文字是灰青色。
- 標題與故事文字用系統可取得的中文字體 serif fallback；控制、標籤與資料用 system sans。沒有外部 web font。
- 卡片偏方正、圓角很小；大量使用小型 uppercase eyebrow、letter spacing、細線、微光與低彩度，形成偏成熟、技術感而非卡通化的氣質。
- 首頁以大標題＋右側建立／加入卡為主；規則與客服沿用同一雙欄 landing shell。遊戲頁資訊密度高，狀態主要透過文字、顏色、顯示／隱藏控制和 disabled state 表達。
- 現有字級普遍偏小（大量 `.65rem`–`.8rem`）；story body 約 `.95rem`、行高 `1.95`。這是現況描述，不代表應保留所有字級。

### 最新 production-facing 文案方向

主 task 的 `0943f08` 已把過時或可能誤導的 `AWS Tier 0`、`AWS 公開試玩`、「本批次」與「本機資料層／本機草稿」移出 production UI。後續建議請沿用以下語意：

- 環境稱為 `AWS Production Demo`／`AWS Production`。
- 敘事稱為由 Amazon Bedrock 執行的非同步 AI 敘事；資料儲存於 private PostgreSQL。
- Support UI 稱「待確認草稿」或「專案資料層」，並始終補充「仍需人工確認、不會對外提交」。
- `local_draft_only` 仍是 API／domain 的固定技術狀態，但不應據此恢復「本機資料層」等與實際 production persistence 不一致的玩家文案。
- 該 commit 也讓 footer 可換行；Claude 應以更新後方向提出建議，不要要求退回舊 footer 文案。

## 4. Support Agent 現有能力與安全邊界

目前 production 已部署 Phase A，但它是 bounded support 工具，不是可自由對話或代辦的通用 Agent。

### 已有能力

1. 匿名規則查詢：輸入 1–500 字，僅從版本化、allowlisted 靜態規則找到唯一依據；supported 答案顯示 canonical answer 與 rule ID、標題、Spec 章節、版本。查無或多重命中時回 unsupported，明確不猜測。
2. 問題回報草稿：僅有效 Player session 可用（同時也是玩家的房主可用；純 Host session 不可）。輸入 1–2000 字後回 sanitized 的分類、摘要、重現步驟、預期／實際結果與 opaque 草稿編號。
3. 草稿固定顯示 `requiresHumanConfirmation=true`、`submissionStatus=local_draft_only`，並保存在 PostgreSQL；相同玩家與相同正規化內容會收斂至同一草稿。

### 不可模糊的邊界

- 沒有外部送出按鈕；草稿未送到 GitHub Issue、Email 或其他客服系統，不能使用「已回報／已送出」文案。
- 沒有 Bedrock、RAG、MCP、任意 tool execution 或自由 route switching。若要加入任一能力，需另立產品與安全邊界，不屬於本次 UI review。
- 規則查詢與草稿建立是兩條固定 intent；UI 不得讓模型把匿名查詢自動轉成有副作用的草稿。
- 草稿必須有 Player cookie、CSRF 與 server-side canonical room/player identity；request body 只能含 `description`。
- unknown tool、額外參數、prompt injection、規則改寫與越界要求 fail closed。敏感內容在 model proposal、草稿與 repository 前先清理；不得顯示 raw exception、runtime metadata、cookie、token、DSN、credential 或 identity digest。
- 可見錯誤需使用固定安全文案。規則查詢每來源每 60 秒最多 10 次；草稿每玩家每 10 分鐘最多 3 次。第一版 limiter 不宣稱跨 process／restart durability。
- static retrieval 目前不能涵蓋所有自然語言問法；unsupported 是預期且安全的結果，不應以誘導性 UI 鼓勵使用者反覆改寫到「猜出答案」。

## 5. Production、CSP、無障礙與 responsive 限制

### 技術與 production

- 前端為 Vanilla JavaScript＋原生 ES modules，無 React、無大型 bundler、無 build step。現階段不應為視覺調整引入框架或新 runtime dependency。
- UI 只能透過同源 `/api/v1` adapter；瀏覽器不得直接連 RDS、Bedrock、SQS 或 AWS SDK。正式資料以後端 Room 為唯一 canonical state。
- Session 使用 `HttpOnly` cookie；mutation 還受 CSRF、room version 與 idempotency 保護。設計稿不能以 local-only state 取代授權或把安全 token 放進可見 UI／JavaScript。
- Production 對 unsafe API request 驗證允許的 Origin，所有 fetch 使用 `credentials: include`。安全 header 包含 `nosniff`、`Referrer-Policy: same-origin`、HSTS、`Cache-Control: no-store`。
- Production CSP 現為 `default-src 'self'; frame-ancestors 'none'`：腳本、樣式、字型與其他資源預設只能同源，頁面不可被 iframe 嵌入。近期已移除 inline script 與 Google Fonts；建議不得依賴 inline script、外部 font/CDN、第三方 iframe 或外站 asset。若提議新圖片／icon，請優先同源靜態資產或既有 CSS／文字符號，並標示 CSP 影響。
- 目前 production 已驗證 Support 頁 rendering 與 Tier 2 `202 → polling → applied result`。主 task 最新文案以 `AWS Production Demo`、非同步 Amazon Bedrock 敘事與 private PostgreSQL 描述這些事實。本 briefing 不授權 production deploy、AWS 呼叫或新的玩家／模型 E2E。

### Accessibility

- 目標最低標準：所有 input 有可見 label；錯誤可被 assistive technology 讀取；鍵盤可完成建立、加入、提交與結算；狀態不能只靠顏色；確認流程需管理 focus。
- 現況已有 `lang="zh-Hant"`、多數 `label`、`role="status"／"alert"`、`aria-live`、部分 `aria-describedby`／`aria-invalid` 與文字狀態。
- 現況仍值得 review 的事實：玩家 ready dot 有 `title` 且旁邊另有文字狀態；進度條以 `div` 寬度呈現、百分比另有文字；部分錯誤顯示後沒有明確 focus-first-error 實作；永久刪除使用瀏覽器原生 `confirm`；許多次要字級與 muted 對比偏保守。
- 建議必須能在不改 canonical 行為的前提下改善 focus order、可讀性、狀態辨識、touch target 與動態訊息，不要用只在 hover 出現的資訊承載必要意義。

### Responsive

- Desktop 是 Demo 主目標；窄螢幕仍須可閱讀且主要操作不能水平溢出。
- CSS 斷點為 `1050px` 與 `720px`：中尺寸把遊戲頁變兩欄並把狀態面板放到底部；手機改為單欄，故事欄排第一，房間與狀態面板接續其後。
- 手機版仍保留高資訊密度、固定感較強的 story 最低高度、雙欄按鈕／表單與 topbar 導覽。CURRENT 只證明 iPhone Safari 的短期雙向同步；長時間 polling／visibility 尚未在完整多人遊戲驗證。

## 6. 不可改變的產品行為

請把下列項目視為 hard constraints，而不是可由視覺設計重新決定的需求：

- 房主也是第一位玩家；正式遊戲固定 3–5 人、4／6／8 回合。房主確認世界後才開放 Lobby；3 人以上且全員完成角色才能開始。
- 角色三屬性各 0–2、總和固定 3；星火起始 1、上限 3。骰點與所有結果由後端規則決定，AI 不能修改。
- 行動在結算前對其他玩家與房主隱藏；進入 rolling 後才一次公開。介面不能用 preview、排行或社交提示洩漏內容。
- 玩家看見骰點後才決定星火；無倒數計時。房主可明確略過未回應者，但不能默默代替玩家選擇。
- 正式進度、危機、成功等級與結局公式不可調整。進度達 100% 時由房主明確選擇立即結局或繼續尾聲。
- AI 失敗時保留已鎖定的 action、骰點與星火，不先提交進度／危機／故事；只有房主可手動 retry 或使用 deterministic fallback。
- Polling 不可變成自動重送 mutation。`RESOLVING` 延遲時不得自動取消、重送 job 或 fallback。
- Session 過期、房間刪除或不存在時不得以 Demo 假資料補畫面；Demo 必須明確隔離且不保存。
- 內容固定為 13+、原創並拒絕 prompt injection／credential 索取；安全限制不能由房主關閉。
- Support 規則答案必須有來源或明確 unsupported；問題草稿永遠是尚未提交、需人工確認的 `local_draft_only`。
- 永久刪除只限房主、只在完成房間可用，且必須清楚確認不可復原。

## 7. 2–3 天內適合的小規模優化範圍

請將建議限制在既有 DOM、CSS 與 page rendering 能完成的小切片，優先排序而非全面 redesign：

1. **遊戲頁的狀態層級與下一步辨識**：讓玩家在高密度三欄／單欄畫面中更快辨識「目前階段、誰能操作、下一步、等待原因」，並釐清 polling、mutation feedback、AI processing、房主控制彼此的層級。
2. **手機與中尺寸可讀性**：檢視 story-first 排序、topbar、composer、雙按鈕、角色／世界表單、狀態面板與 footer；以不改流程的 CSS／markup 微調降低捲動迷失、水平壓縮與誤觸。
3. **Support 頁的信任與結果呈現**：改善 supported citation、unsupported、匿名／Player capability、loading／rate limit，以及「只建立草稿、尚未送出」的視覺區隔；不得新增聊天隱喻或送出能力。
4. **Accessibility 快速修正**：字級／對比、focus-visible、送出後 focus、第一個 validation error、live region 節奏、進度語意與 touch target。請區分「可在 2–3 天落地」與「需另開行為／測試切片」。
5. **視覺一致性整理**：在保留夜色劇場語言下，收斂按鈕優先級、狀態色、卡片間距、heading scale 與表單節奏；不新增外部字型、框架或品牌重做。

不在此範圍：新遊戲規則、新頁面流程、Support Phase B、RAG／Bedrock、外部 submit、WebSocket、帳號系統、API／資料庫／AWS 變更、production deployment、完整 design system 或大規模前端重寫。

## 8. 請 Claude 具體回覆

請以繁體中文回答，先列問題再列方案，並明確標示事實、推論與需驗證假設：

1. 依「玩家卡住的風險 × 2–3 天可落地性」排序目前最重要的 5 個 UI／UX 問題；每項指出頁面、狀態、受影響角色與判斷依據。
2. 為優先前三項提供具體 before／after 建議：資訊層級、文案、元件狀態、focus／鍵盤行為、桌面與手機差異；不要只給風格形容詞。
3. 對遊戲頁提出一份最小狀態呈現矩陣，至少涵蓋一般等待、可操作、提交中、離線、`RESOLVING` 超過 60 秒、`RESOLUTION_FAILED`、session expired 與 `COMPLETED`，並避免把 polling status、mutation feedback 與 AI status 混為一談。
4. 對 Support 頁提出 grounded answer、unsupported、無 Player capability、草稿成功與 rate limited 五種狀態的呈現建議；每種都要保持「規則不猜測」「草稿未提交」安全語意。
5. 指出現有 dark theme 在文字尺寸、對比、focus、touch target、scroll／reading order 上最可能的 accessibility／responsive 風險，並提供不依賴外部字型、inline script 或第三方 asset 的修正方向。
6. 給出一個最多 3 個實作切片的順序，每片列出：預期檔案範圍、可觀察驗收條件、需補的 UI tests／browser checks，以及任何可能碰到產品或安全邊界而必須停止確認的項目。

若需要做視覺稿，請只提供低擬真 wireframe／元件層級描述；不要假設可改 API schema、房間狀態機、授權、rate limit、CSP 或 AWS 架構。
