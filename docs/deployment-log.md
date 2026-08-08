# 部署紀錄

本文件用來記錄每次 AWS 建置、修改、測試與 Demo 準備。講師或面試官詢問「你做了什麼、為什麼這樣做」時，可用此文件回溯。

## 基本資訊

| 項目 | 內容 |
| --- | --- |
| 專題名稱 | 共演計劃：多人 AI 故事遊戲 |
| 主線題目 | 同一產品累積完成 Tier 0–5 |
| 演進內容 | Web／DB 分離、可觀測性、SSM、分層架構、CI/CD、微服務、RAG、MCP、Agentic AI |
| 期末專題繳交日 | 2026-09-07 |
| AWS Region | Asia Pacific (Tokyo) — `ap-northeast-1` |
| VPC CIDR | 待確認 |
| Public Subnet CIDR | 待確認 |
| Private Subnet CIDR | 待確認 |
| EC2 規格 | 待確認 |
| 資料層規格 | 待確認 |

## 變更紀錄

| 日期 | 階段 | 變更內容 | 驗證方式 | 截圖 |
| --- | --- | --- | --- | --- |
| 2026-07-15 | Phase 0 | 建立專題文件、Agent 規範、架構圖與截圖目錄 | GitHub repository 文件可讀 | 待補 |
| 2026-08-06 | Phase 0 | 建立專題 Agent Skill 與 AWS 唯讀盤點工具 | 官方 Skill validator、Shell 語法與最小觸發靜態檢查通過 | [Skill 驗證](evidence/2026-08-06-skill-and-iam/skill-validation.md) |
| 2026-08-06 | IAM 前置 | 檢查 AWS CLI／Console 登入狀態；未取得憑證前停止 AWS 寫入 | CLI 無 profile／Region／AWS 環境憑證，Console 需登入 | [前置盤點](evidence/2026-08-06-skill-and-iam/aws-cli-preflight.md) |
| 2026-08-07 | P0-1 | 驗證 Budget、Root MFA、Root Access Key、Organizations、Region 與 CloudTrail | Console 截圖及 CloudTrail Event history | [帳號安全前置驗證](evidence/2026-08-07-p0-1-account-security/inventory-summary.md) |
| 2026-08-07 | IAM Identity Center 前置 | 確認尚未啟用，完成 organization instance 啟用前成本、安全、Region 與回復關卡；拒絕預選的 multi-Region KMS 計費方案 | Console 顯示 Tokyo 啟用頁及 KMS 成本警告；尚未執行 AWS 寫入 | [啟用前關卡](evidence/2026-08-07-identity-center/enable-preflight.md) |
| 2026-08-07 | IAM Identity Center | 經使用者確認，以 Root 在 Tokyo 啟用單一區域 organization instance；使用 AWS owned key，無其他 Region | 去識別化 Dashboard 顯示 Identity Center directory 與主要 Region `ap-northeast-1` | [啟用結果](evidence/2026-08-07-identity-center/enable-result.md)／[截圖](screenshots/phase0-identity-center-enabled.png) |
| 2026-08-07 | IAM Identity Center group | 建立空白 `AWSFinalProjectDevelopers` group；未建立任何 account／application assignment | Group 詳細畫面顯示成員數 `0` | [Group 建立結果](evidence/2026-08-07-identity-center/group-result.md) |
| 2026-08-07 | Identity Center user | 建立 `ming_dev_finalproject`、加入 `AWSFinalProjectDevelopers` 並完成首次登入；Email 仍顯示未驗證、MFA 為 0 | 使用者已啟用且有 1 個作用中工作階段；待完成 Email／MFA | [User 狀態](evidence/2026-08-07-identity-center/user-result.md) |
| 2026-08-07 | 成本治理 | 收到 Free plan 自動升級 Paid plan 通知；確認由建立 AWS Organization 觸發 | 對照 CloudTrail `CreateOrganization` 與 AWS Free Tier FAQ；原始通知含 account ID 不入庫 | [Account plan 變更](evidence/2026-08-07-p0-1-account-security/account-plan-change.md) |
| 2026-08-07 | 流程矯正 | 暫停專題 AWS 寫入；在 Skill 與 handoff 增加 Account plan／Credits 硬性關卡 | 本機文件檢查；待提交 AWS Support 帳務案件 | [根因與矯正](evidence/2026-08-07-p0-1-account-security/account-plan-change.md) |
| 2026-08-07 | 產品設計 | 完成 LLM 文字 RPG research、15 項 grill-me 決策與正式 MVP Spec；AWS 部署持續延後 | 需求可追溯性、Markdown 與連結檢查；未執行 AWS 寫入 | [MVP Spec](specs/text-rpg-mvp-spec.md)／[Research](research/llm-text-rpg.md) |
| 2026-08-07 | Web 架構評估（已更正） | 專題暫定更名為「共演計劃」；比較 WordPress 與自製 Web App。當時把 WordPress 列為選配入口的建議已由課程要求更正取代 | 官方文件、現有原型與 MVP Spec 差距分析；未執行 AWS 寫入 | [Web 平台評估](research/wordpress-web-platform-evaluation.md) |
| 2026-08-07 | 課程要求對齊（已更正） | 逐頁檢查 53 張期末專題投影片後，最初曾誤建議「P0-2 WordPress 保底＋共演計劃加值」；此解讀已由下一筆紀錄取代 | 原始 PPT、逐頁 render 與文字／版面檢查；未執行 AWS 寫入 | [課程要求對照](course-requirements-alignment.md) |
| 2026-08-07 | 課程要求解讀更正 | 依講師補充、`AGENTS.md` 與 Project Brief，確認 Tier 0–5 不是選擇題；改為「共演計劃」同一產品逐層演進，每一 Tier 均保留 AWS 實作、Demo 與證據 | 交叉檢查專題簡報、Agent 指引、Project Brief 與全案文件；未執行 AWS 寫入 | [課程要求對照](course-requirements-alignment.md)／[專題規劃](project-plan.md) |
| 2026-08-08 | 前端架構設計 | 接受 Clean Architecture：UI／Application／Domain 向內相依，`GameApi` 隔離 Mock 與 FastAPI，瀏覽器不直接存取 AWS 服務或 credential | ADR、分層、狀態、AWS 演進、測試與遷移條件文件檢查；未執行 AWS 寫入 | [前端架構](architecture/frontend-clean-architecture.md)／[ADR-0002](decisions/0002-adopt-clean-frontend-architecture.md) |
| 2026-08-08 | 前端 vertical slice | 將單一 `app.js` 拆為 ES modules、Domain／Application／Adapters／UI／Composition；建立 `GameApi`、記憶體 `MockGameApi`、建立／加入／提交 use cases，移除遊戲 state 的 `localStorage` 持久化 | 9 項 Node tests 通過；瀏覽器建立房間與加入玩家 smoke test 通過；Console 0 errors；未執行 AWS 寫入 | [驗證證據](evidence/2026-08-08-frontend-vertical-slice/validation.md)／[今日進度](daily/2026-08-08.md) |
| 2026-08-08 | FastAPI vertical slice | 建立 health、memory repository、`Storyteller` port、`MockStoryteller`、同源靜態服務與 `FetchGameApi`；以 `HttpOnly` local room cookie 恢復目前房間 | 後端 5 tests、前端 12 tests、FastAPI 瀏覽器建房／加入／refresh smoke test 通過；初次測試發現並修正 browser fetch binding；未執行 AWS 寫入 | [驗證證據](evidence/2026-08-08-fastapi-vertical-slice/validation.md)／[LLM 串接設計](architecture/llm-integration.md) |
| 2026-08-08 | Session 安全 vertical slice | 建立 host／player opaque session hash、player CSRF、scoped idempotency 與 action owner server authorization；未結算 action 不向其他玩家揭露 | 後端 10 tests、前端 15 tests、Browser 匿名拒絕／加入／提交／refresh 正面驗證；Console 0 errors；未執行 AWS 寫入 | [驗證證據](evidence/2026-08-08-session-security/validation.md)／[安全設計](architecture/session-and-idempotency.md) |
| 2026-08-08 | Host 世界與 Lobby vertical slice | 實作 `DRAFT → LOBBY → COLLECTING_ACTIONS`、直接輸入世界、4／6／8 回合與 host-only start；host mutation 使用獨立 CSRF、version 與 idempotency | 後端 13 tests、前端 19 tests；Browser 建房、確認世界、房主兼玩家、0／1 人 start disabled、Console 0 errors；初次 Browser 驗證發現並修正 busy cleanup 重新啟用按鈕；未執行 AWS 寫入 | [驗證證據](evidence/2026-08-08-host-lobby-flow/validation.md) |
| 2026-08-08 | 角色建立與配點 vertical slice | 建立 player-only 角色 mutation、名稱／背景／特質／弱點、勇氣／洞察／羈絆三點配點與固定 1 星火；Lobby start 要求全員角色完成 | 後端 14 tests、前端 22 tests；Browser 建房→確認世界→加入→`2/1/0` 配點→角色 ready，Console 0 errors；8000 Demo 與 8765 驗證伺服器皆已停止；未執行 AWS 寫入 | [驗證證據](evidence/2026-08-08-character-creation/validation.md) |

## AWS Budget Alarm

| 項目 | 狀態 |
| --- | --- |
| 是否已建立 | 已驗證，運作狀態正常 |
| 預算金額 | 每月 `US$1.00` |
| 目前支出 | `US$0.00`（2026-08-07 驗證） |
| 通知設定 | 提醒閾值已確認；Email 位址未保存於證據 |
| 截圖 | [phase0-zero-spend-budget-verified.png](screenshots/phase0-zero-spend-budget-verified.png) |

## 2026-08-06：Agent Skill 與 IAM

| 項目 | 狀態 | 證據／下一步 |
| --- | --- | --- |
| 專題 Agent Skill | 已建立並通過結構驗證 | [Skill 驗證](evidence/2026-08-06-skill-and-iam/skill-validation.md) |
| AWS principal／account／Region | Root user；Organizations management account；Tokyo `ap-northeast-1` | 帳號 ID 未保存；[P0-1 證據](evidence/2026-08-07-p0-1-account-security/inventory-summary.md) |
| IAM Identity Center | 已在 Tokyo 啟用單一區域 organization instance | [啟用結果](evidence/2026-08-07-identity-center/enable-result.md)／[截圖](screenshots/phase0-identity-center-enabled.png) |
| Root MFA／Budget／CloudTrail | 已由 Console 即時驗證 | [P0-1 證據](evidence/2026-08-07-p0-1-account-security/inventory-summary.md) |
| Identity Center group | 已建立 `AWSFinalProjectDevelopers`；目前 0 位成員、無 assignment | [Group 建立結果](evidence/2026-08-07-identity-center/group-result.md) |
| Identity Center user／permission set／assignment | 尚未建立 | [預定變更集](evidence/2026-08-06-skill-and-iam/proposed-iam-change-set.md) |
| `AWSFinalProjectAppRole` | 尚未建立 | 確認 EC2、資源 ARN 與 policy 邊界後建立 |
| Lambda／GitHub deploy／Operator roles | 本日不建立 | 當前架構尚未需要 |
| 長期 Access Key | 本次未建立 | 人員存取採 Identity Center 與短期 SSO 憑證 |

費用影響：目前只有本機文件與唯讀工具，未建立 AWS 計費資源。

回復方式：刪除專案 Skill 與本日證據文件即可回復本機變更；AWS 尚無需回復的寫入。

## 2026-08-07：P0-1 帳號安全前置驗證

- 驗證 Root user 已啟用 MFA，且沒有作用中的 Root Access Key。
- 驗證 `My Zero-Spend Budget` 每月預算為 `US$1.00`、目前支出為 `US$0.00`，運作狀態正常。
- 確認專題 Region 為 Tokyo `ap-northeast-1`；IAM 為 Global 服務，IAM 頁面無法切換 Region 屬正常行為。
- 確認 AWS Organizations 已啟用，登入帳號為 management account。
- CloudTrail Event history 可查到 Root 的 `ConsoleLogin`；Root 登入事件位於 `us-east-1`。
- 稽核發現驗證期間曾建立 AWS Organization，相關 `CreateOrganization`、`AccountJoinedOrganization`、policy 與 service-linked role 事件已保存。Organizations 保留供後續 IAM Identity Center 使用。

費用影響：AWS Organizations 本身不另收服務費，但建立 Organization 已使 Free account plan 自動升級為 Paid plan，相關 Free Tier credits 依官方規則立即失效且無法降級；詳見[帳號方案變更紀錄](evidence/2026-08-07-p0-1-account-security/account-plan-change.md)。本階段未建立 EC2、RDS、NAT Gateway 或其他專題計費資源。

安全邊界：未建立長期 Access Key；未授予任何應用程式 `AdministratorAccess`。完成 Identity Center 後應停止以 Root user 進行日常操作。

證據：[P0-1 帳號安全前置驗證摘要](evidence/2026-08-07-p0-1-account-security/inventory-summary.md)

## 封存模板：WordPress Web/DB 分離

以下是 ADR-0001 前的舊模板，只保留歷史追溯，不代表目前選定架構，也不得作為後續 Agent 的執行指引。新的 Tier 0 驗收以[架構文件](architecture/README.md)與[課程要求對照](course-requirements-alignment.md)為準。

### VPC

| 項目 | 設定 |
| --- | --- |
| VPC ID | 待補 |
| CIDR | 待補 |
| Public Subnet | 待補 |
| Private Subnet | 待補 |
| Internet Gateway | 待補 |
| NAT Gateway | 待評估 |

### EC2 WordPress

| 項目 | 設定 |
| --- | --- |
| Instance ID | 待補 |
| AMI | 待補 |
| Instance Type | 待補 |
| Public IP / DNS | 待補 |
| Security Group | 待補 |

### RDS MySQL

| 項目 | 設定 |
| --- | --- |
| DB Identifier | 待補 |
| Engine | MySQL |
| Instance Class | 待補 |
| Public Access | 必須為 No |
| Security Group | 只允許 Web SG 連 3306 |

## 驗收紀錄

| 檢核項目 | 狀態 | 證據 |
| --- | --- | --- |
| WordPress 可公開瀏覽 | 待驗證 | 待補 |
| RDS 位於 private subnet | 待驗證 | 待補 |
| DB 無法被外網直接連線 | 待驗證 | 待補 |
| Web SG 可連 DB:3306 | 待驗證 | 待補 |
| WordPress 發文後資料仍存在 | 待驗證 | 待補 |

## Demo 筆記

待補。
