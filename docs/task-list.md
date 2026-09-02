# 共演計劃：最終交付任務清單

期末專題繳交日：2026-09-07。

本清單只追蹤依 [ADR-0008](decisions/0008-fix-final-delivery-scope.md) 固定的最終交付與證據收斂。Tier 0–3 名稱僅作已實作能力對照；Tier 4／5 是 future roadmap，不得由歷史未勾項推導為目前 backlog。AWS 寫入仍須遵守帳號、Budget、估價、principal 與清理關卡。

## A. AWS 帳號與費用

- [x] 舊帳號 AWS Billing Support 禮貌性點數申請已隨切換帳號失去適用性，不是 Demo 或交付阻斷項。
- [x] 已確認最終部署帳號、account plan、credits 與責任歸屬；除非 change envelope 擴張，不重複盤點。
- [x] 已確認不建立／加入 AWS Organizations。
- [x] 已確認 Budget、目前費用、Region、principal 與既有資源；除非 change envelope 擴張，不重複盤點。
- [ ] 保存逐項估價、最大可接受預算與清理方式。

## B. 產品與本機 MVP

- [x] 完成 LLM 多人故事遊戲 Research。
- [x] 完成 15 項需求訪談並核准正式 MVP Spec。
- [x] 完成 Web App 流程補充 Grill；只補足既有 Spec 未定義的 Host／Player、Demo、轉移碼、期限與 LLM failure UX。
- [x] 建立輕量 source-of-truth、User Flow、Screen States、Feature Spec 與本機 MVP Test Plan。
- [x] 暫定產品名稱為「共演計劃」，支援職場、日常、校園、科幻與奇幻等題材。
- [x] 建立 Vanilla HTML／CSS／JavaScript 展示原型。
- [x] 接受前端 Clean Architecture、`GameApi` port 與後端 API 安全邊界。
- [x] 已確認並部署 Vanilla JS＋FastAPI＋PostgreSQL 技術路線。
- [x] 建立 ES modules、composition root 與 Domain／Application／Adapter／UI 目錄。
- [x] 建立 `GameApi` contract、`MockGameApi` 與原型 create／join／submit use case tests。
- [x] 將既有原型 canonical state 從 `localStorage` 移到記憶體 Mock adapter。
- [x] 將原型 DOM 邏輯移入 UI page 與 presenter，完成第一階段分層。
- [x] 正式 `/` 已顯示建立／加入 Landing，且不建立 Demo state 或啟動 room polling。
- Future refactor：可將 Lobby／Play／Ending 從大型 `GamePage` 進一步拆分；不影響目前 production 行為或 final delivery。
- [x] 將開發用 `BONUS7` Demo 隔離至 `/demo`；正式 `/` 不自動載入 Demo。
- [x] 建房時原子性建立 Host session、房主 Player 與 Player session，房主計入 3–5 位玩家。
- [x] 建立依 room code＋暱稱原子性加入的 API／adapter／UI 與拒絕案例。
- [x] 建立有效 session 的「繼續目前遊戲」與 deep-link refresh。
- [x] 建立 FastAPI skeleton、health endpoint 與同源靜態檔案服務。
- [x] 建立 World／Room／Player／Character／DiceResult domain models。
- [x] 建立至 `AWAITING_SPARK` 的 state machine 與 `2d6 + 屬性` deterministic engine。
- [x] 完成星火 USE／DECLINE、房主略過等待者與 deterministic 結果重算。
- [x] 完成正式進度／危機套用、星火增減、Mock 敘事與下一回合推進。
- [x] 完成 4／6／8 回合上限、提前完成、房主選擇與結局狀態。
- [x] 建立 repository 與 storyteller interfaces。
- [x] 建立 memory repository、mock storyteller 與 API 自動測試。
- [x] 建立 `FetchGameApi`，將目前 create／join／submit mutation 與 canonical state 改由 API 管理。
- [x] 建立 host／player opaque session；後端只保存 token hash。
- [x] Action 使用 player session＋CSRF，前端不可指定任意 `player_id`。
- [x] Create／world／join／character／start／action／roll mutation 實作 scoped `Idempotency-Key`。
- [x] 未結算 action 只揭露提交狀態，不揭露其他玩家文字。
- [x] 建立 `DRAFT → LOBBY → COLLECTING_ACTIONS → AWAITING_HOST → AWAITING_SPARK → RESOLVING → COLLECTING_ACTIONS` 狀態轉移。
- [x] 世界確認與開始遊戲使用 host session＋CSRF＋version＋idempotency。
- [x] Lobby 僅允許 3–5 位玩家由房主開始，非房主與人數不足請求會被拒絕。
- [x] 建立 player-only 角色 mutation 與角色名稱、背景、特質、弱點欄位。
- [x] 勇氣／洞察／羈絆各限制 0–2 且總和為 3，星火由後端固定為 1。
- [x] Lobby start 要求 3–5 位玩家全數完成角色。
- [x] Action 支援勇氣／洞察／羈絆，擲骰前隱藏、擲骰後一次揭露。
- [x] Host-only roll 使用 CSPRNG，並保存原始骰點、結果與待結算進度／危機。
- [x] 完成無重疊的 room polling、完成結局停止與 timer 取消。
- [x] PR #65以strict TDD清除async terminal Room後殘留的AI pending feedback，並移除沒有room-code rotation contract的建立新房間控制；後續 production release 已包含此修正。
- [x] 完成 polling 離線重試、connection 狀態與前端錯誤提示。
- [x] 完成 Loading／Empty／Validation／Session expired／Version conflict 等共通 Screen States。
- [x] 完成 room version 與 mutation idempotency 基礎邊界。
- [x] 完成 Mock／HTTP adapter 的目標點數、提前完成與最大回合結局 contract tests。
- [x] 完成房主略過未提交 action 的正式 UI／API 行為。
- [x] 完成 10 分鐘一次性角色轉移碼、舊 session revoke 與負面測試。
- [x] 完成最後活動／結局後 7 天到期、房主永久刪除與 maintenance cleanup。
- [x] 完成世界草稿生成上限、保留輸入與手動輸入 fallback。
- [x] 完成回合 LLM 自動／手動 retry、deterministic fallback 與安全 telemetry。
- [x] 完成三個獨立 Browser session 的三玩家 E2E。
- [x] 第一輪 AWS smoke 後改善世界生成 UX：關鍵字接受 `、`／`，`／`,`、按鈕附近 loading／安全失敗訊息、canonical loading shell、泛用行動範例與 AWS runtime 文案已部署，Batch 9B Browser 驗證通過（`d2b76ba`、`f9d4155`）。

## C. Tier 0：AWS 可玩傳統架構

- [x] 講師已確認自製 FastAPI＋private PostgreSQL 可作 Web／DB 分離等效實作與課程對映。
- [x] 建立 VPC、public subnet、private DB subnets、route table 與 IGW。
- [x] 建立 App SG 與 DB SG；DB port 來源只允許 App SG。
- [x] 建立 private PostgreSQL／RDS 與 app database。
- [x] 建立最小權限 EC2 app role；不含管理員或服務 Full Access。
- [x] 建立單台小型 EC2、Nginx、FastAPI；不開 public SSH。
- [x] 建立 Bedrock adapter並限制 model、token、timeout 與 retry。
- [x] 部署 application-layer 明確 Prompt Injection 前置拒絕；Red `a3f12a8`／Green `6f872b2`，Batch 9D 以 API `422`、次數不扣除與零 Storyteller failure event 通過 AWS Browser 驗證。
- [x] 驗證 3 位玩家完成一回合、refresh 後資料存在。
- [x] 完成四玩家四回合外部公開試玩；Bedrock 六次呼叫、private RDS connection、EC2 低負載、HTTP 無 `5xx` 與刪房成功均有 sanitized evidence。
- [x] 驗證 private DB／Data 外網不可達與未知 principal 的 Bedrock 最小權限負面邊界。
- [x] 已保存 sanitized 的公開 Web、VPC、subnet、SG、DB、IAM 與遊戲成功證據；公開 URL／IP 不入庫。

## D. Tier 1：可觀測性、AIOps、SSM

- [x] 建立 CloudWatch application／system logs、metrics、dashboard 與 alarm。
- [x] 記錄 HTTP error、LLM latency、token、retry、fallback 與估計成本。
- [x] 以 Session Manager 登入，證明 `22/tcp` 未開放。
- [x] 以 Run Command 執行受控 health／restart 操作。
- [x] 建立最小 AIOps Agent，讀取 logs 並摘要 root cause／建議動作。
- [x] 模擬一次 500 或 DB 連線失敗，完成偵測→判讀→人工批准→修復 Demo。

## E. Tier 2：三組件切割

- [x] 建立 Web/API、Story Worker、Data 依賴圖，並完成PostgreSQL durable story-job local contract。
- [x] 將故事生成改為 queue／job 模式並保存 idempotency key。
- [x] 部署至少三個課程要求可辨識的 AWS 組件／compute，公私網段正確。
- [x] Data 與 Worker 不直接對外；SG 只允許必要流量。
- [x] 驗證 action→queue→worker→Bedrock→database→result E2E。
  - [x] Production玩家流程完成`202 → polling → applied result`；retry batch精確一次dispatch／一次Bedrock invocation，Room進入Round 02／`COLLECTING_ACTIONS`，Queue／DLQ回空。
- [x] 保存組件、網段、SG 與負面連線證據。

## F. Tier 3：CI/CD

- [x] 建立 runtime-only multi-stage Dockerfile 與本機 container tests；PR #8 的 GitHub container build／Trivy gate 通過。
- [x] 建立 immutable、scan-on-push ECR repository 與 lifecycle policy；failed與successful ARM64 images均可由exact digest追溯，lifecycle limit為10。
- [x] 建立 GitHub OIDC deploy role，trust policy 限定 exact repository／`main`，並通過正負控制。
- [x] GitHub Actions已完成test、OIDC、ARM64 build、immutable push與exact-digest Trivy，並以三次fail-closed驗證安全停止。
- [x] 自動部署至 EC2 container runtime，保留GitHub `production`人工批准、最小權限OIDC role與SSM health／rollback gate。
- [x] HEALTHCHECK程式修正以`digest-release`自動上線，公開live／ready與Docker `healthy` postflight均通過並保存pipeline證據。

## G. Future Tier 4：五個微服務（本次範圍外）

- Lobby／Character／Turn／Rules／Story 五服務與故障隔離保留為 future roadmap。
- 不把本節列為未完成、Demo 阻斷項或近期優先序；啟動前須重新核准範圍與成本。

## H. 已部署的 bounded Support Agent extension

- [x] 建立bounded Support Agent核心、static cited rules、prompt／tool guard、敏感資料清理與PostgreSQL `local_draft_only`草稿持久化／並行耐久性。
- [x] 依固定integration contract完成Support Agent API／session／CSRF／rate limit與Web人工確認UI；不接Bedrock或外部submit。
- [x] 將 bounded Support Agent extension 部署至 production，完成 supported／unsupported 規則查詢、Player 草稿、健康檢查與無 external submit smoke。
- [x] 移除production inline script與Google Fonts外部依賴，在不放寬CSP下完成新digest部署與Browser Console驗證。

完整 Tier 5 的 Prompt A/B、RAG、MCP／tools、多 Agent 與 AI observability 是 future roadmap，不是本節未勾待辦。此 extension 的完成邊界就是已驗證的 citation、拒答、敏感資料清理、rate limit、`local_draft_only` 與人工確認；沒有 Bedrock、RAG 或 external submit。

## H-1. Production UI、像素Widget與寵物規則助手 refresh

- [x] 完成中性`Release v1.1.0`識別、新同源品牌SVG、終端敘事visual hierarchy與reduced-motion邊界。
- [x] 先將既有bounded Support Agent包裝成保留當前頁面的純CSS像素Widget，再以寵物式史萊姆、六個規則主題與自然語言查詢取代玩家`/support`頁；citation／拒答／人工確認安全語意與Backend API保留。
- [x] 完成寵物規則助手整合Frontend `127/127`、desktop／tablet／390px QA、main CI與exact-digest production release；active Web為`sha256:14d8e0f…`、runtime維持`async`。
- [x] 修復Direct IP憑證renewal事故：只授予Nginx父目錄穿越ACL，renewal與strict TLS三端點成功；未rollback Web image。
- [ ] 以strict TDD將ACME父目錄最小權限、challenge probe與憑證到期／renewal failure觀測固化至repo，並在不手動重複renew的前提下觀察下一次timer結果。

## I. 文件、證據與 Demo

- [x] 逐頁檢查 53 張課程簡報並更正 Tier 0–5 解讀。
- [x] 建立 MVP Spec、Research 與課程對照。
- [x] 完成已實作最終範圍的 production architecture diagram；future roadmap 已明確標示範圍外。
- [x] 已實作最終範圍已有成功與必要負面測試的 canonical evidence 索引。
- [x] 同步 README、project plan、gantt、checkpoints、deployment log 與截圖索引的交付範圍口徑。
- [x] 盤點工作區內檔名帶 ` 2` 的未追蹤副本：96份均有canonical，94份逐byte相同，2份為Git歷史中的舊版；已移至`/private/tmp`可恢復備份並重驗tracked diff、未追蹤清單與branch boundary。
- [ ] 建立 5–8 分鐘主 Demo 與完整證據附錄。
- [ ] Demo 後依清理清單停止或刪除資源並驗證帳單。

## 近期順序

| 優先 | 任務 | AWS 寫入 |
| --- | --- | --- |
| 1 | 完成 5–8 分鐘 final Demo 腳本與演練 | 否 |
| 2 | 收斂 production 架構圖與 evidence 索引 | 否 |
| 3 | 完成 repo secrets 與 screenshots 去識別化稽核 | 否 |
| 4 | 完成 2026-09-08 資源清理 runbook 與責任清單 | 否 |
| 5 | 固化ACME最小權限與憑證renewal防回歸，再完成最終文件同步 | 需要獨立核准後才部署修正 |
