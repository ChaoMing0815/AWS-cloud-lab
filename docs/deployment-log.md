# 部署紀錄

本文件用來記錄每次 AWS 建置、修改、測試與 Demo 準備。講師或面試官詢問「你做了什麼、為什麼這樣做」時，可用此文件回溯。

## 基本資訊

| 項目 | 內容 |
| --- | --- |
| 專題名稱 | 共演計劃：多人 AI 故事遊戲 |
| 主線題目 | 同一產品完成 AWS 可玩 MVP、可觀測／SSM、Web／Worker／Data 組件化與自動部署 |
| 演進內容 | 本次交付為 Web／DB 分離、可觀測性、SSM、非同步分層架構與 CI/CD；Tier 4／5 是 future roadmap |
| 期末專題繳交日 | 2026-09-07 |

> 本表下方是不可改寫的時間序部署紀錄；早期「Tier 0–5 全部完成」敘述已由 [ADR-0008](decisions/0008-fix-final-delivery-scope.md) 取代，不得據此建立目前 backlog。
| AWS Region | Asia Pacific (Tokyo) — `ap-northeast-1` |
| VPC CIDR | `10.20.0.0/16` |
| Public Subnet CIDR | `10.20.10.0/24` |
| Private Subnet CIDR | `10.20.110.0/24`、`10.20.120.0/24` |
| EC2 規格 | AL2023 ARM64 `t4g.micro`、8 GiB encrypted gp3、SSM、無 SSH |
| 資料層規格 | PostgreSQL `18.3`、Single-AZ `db.t4g.micro`、20 GiB gp2、private-only、encrypted |

## 變更紀錄

| 日期 | 階段 | 變更內容 | 驗證方式 | 截圖 |
| --- | --- | --- | --- | --- |
| 2026-07-15 | Phase 0 | 建立專題文件、Agent 規範、架構圖與截圖目錄 | GitHub repository 文件可讀 | 待補 |
| 2026-08-06 | Phase 0 | 建立專題 Agent Skill 與 AWS 唯讀盤點工具 | 官方 Skill validator、Shell 語法與最小觸發靜態檢查通過 | [Skill 驗證](evidence/2026-08-06-skill-and-iam/skill-validation.md) |
| 2026-08-06 | IAM 前置 | 檢查 AWS CLI／Console 登入狀態；未取得憑證前停止 AWS 寫入 | CLI 無 profile／Region／AWS 環境憑證，Console 需登入 | [前置盤點](evidence/2026-08-06-skill-and-iam/aws-cli-preflight.md) |
| 2026-08-07 | P0-1 | 驗證 Budget、Root MFA、Root Access Key、Organizations、Region 與 CloudTrail | Console 截圖及 CloudTrail Event history | [帳號安全前置驗證](evidence/2026-08-07-p0-1-account-security/inventory-summary.md) |
| 2026-08-07 | IAM Identity Center 前置 | 確認尚未啟用，完成 organization instance 啟用前成本、安全、Region 與回復關卡；拒絕預選的 multi-Region KMS 計費方案 | Console 顯示 Tokyo 啟用頁及 KMS 成本警告；尚未執行 AWS 寫入 | [啟用前關卡](evidence/2026-08-07-identity-center/enable-preflight.md) |
| 2026-08-07 | IAM Identity Center | 經使用者確認，以 Root 在 Tokyo 啟用單一區域 organization instance；使用 AWS owned key，無其他 Region | 舊帳號文字事故紀錄；相關截圖已於 2026-08-10 清除，不能作為目前環境證據 | [啟用結果](evidence/2026-08-07-identity-center/enable-result.md) |
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
| 2026-08-08 | Deterministic 回合裁定 vertical slice | 建立 action approach、`DiceRoller` port、`2d6 + 屬性` 三段判定、待結算進度／危機，以及 `AWAITING_HOST → AWAITING_SPARK`；擲骰限房主且具 CSRF、version、idempotency | 後端 16 tests、前端 24 tests；固定骰驗證三種結果、重送不重擲；Browser 顯示屬性與骰點區、Console 0 errors；8765 已停止；未執行 AWS 寫入 | [驗證證據](evidence/2026-08-08-deterministic-rules/validation.md) |
| 2026-08-09 | 星火與完整單回合 vertical slice | 建立 player-only 星火決策、host-only 結算／略過等待者、正式點數與星火套用、Mock 敘事及下一回合；前端加入決策與結算控制 | 後端 18 tests、前端 28 tests；三玩家固定骰整合、授權／CSRF／無星火／pending／replay 負面驗證；Browser Console 0 errors；8765 已停止；未執行 AWS 寫入 | [驗證證據](evidence/2026-08-09-spark-round-resolution/validation.md) |
| 2026-08-09 | 開發流程治理 | 稽核既有測試歷史，確認過去屬測試規劃先行但非可稽核嚴格 TDD；後續程式行為改採 Red／Green／Refactor、test-first 證據與 mutation 敏感度驗證 | 文件交叉檢查、Git 歷史稽核與規範連結檢查；未修改 production code、未執行 AWS 寫入 | [TDD 採用紀錄](evidence/2026-08-09-tdd-governance/adoption.md) |
| 2026-08-09 | 回合上限與結局策略 | 以四組嚴格 Red／Green 循環完成 4／6／8 回合上限、正式百分比、提前完成、host-only `FINISH_NOW／CONTINUE`、自動結局敘事與前端結局控制 | 後端 `28 passed`、前端 `35 passed`；三項 mutation 敏感度測試；Browser Console 0 errors、無水平溢出；8765 已停止；未執行 AWS 寫入 | [嚴格 TDD 驗證](evidence/2026-08-09-ending-policy/tdd-validation.md) |
| 2026-08-09 | Mock／HTTP 結局合約一致性 | Mock adapter 對齊目標點數、百分比、提前完成與最大回合自動結局；立即結局共用完成流程 | Red `3 failed`；Green 後端 `28 passed`、前端 `38 passed`；最大回合 operator mutation 正確失敗；未啟動伺服器或執行 AWS 寫入 | [TDD 驗證](evidence/2026-08-09-mock-ending-parity/tdd-validation.md) |
| 2026-08-09 | 房間狀態 polling | 以串行 3 秒 polling 更新 canonical state；避免重疊 request，完成結局或停止時不再排程 | Red `4 failed`；Green 後端 `28 passed`、前端 `42 passed`；移除 in-flight guard 的 mutation 正確失敗；Browser 觀察多次 `/rooms/current` 200、Console 0 errors；8765 已停止；未執行 AWS 寫入 | [TDD 驗證](evidence/2026-08-09-room-polling/tdd-validation.md) |
| 2026-08-09 | Web App 流程治理 | 依既有 MVP Spec 補足 Host／Player、Demo、角色轉移、期限與 LLM failure UX；建立輕量 source-of-truth、User Flow、Screen States、入口 Feature Spec 與本機 Test Plan | 文件權威與連結一致性檢查；本階段未修改 production code、未啟動服務、未執行 AWS 寫入 | [權威索引](product/source-of-truth.md)／[入口 Feature Spec](features/entry-and-room-join.md) |
| 2026-08-09 | 正式 Landing 第一切片 | 以三組 Red／Green 建立正式根頁、隔離 `/demo`、補 FastAPI app shell route，並修正 Browser 發現的 hidden CSS 回歸 | Backend `29 passed`、Frontend `44 passed`；Browser 驗證 root／demo visibility、`/demo` 200、Console 0 errors；本機 server 已停止，未執行 AWS 寫入 | [TDD 驗證](evidence/2026-08-09-formal-entry/tdd-validation.md) |
| 2026-08-09 | 房主建房 WP-1B | 建房時原子性建立 Host／Player 雙 session 與第一位玩家；Landing 串接 API 並導向 `/host/setup`；拒絕 client-supplied `player_id` | Backend `34 passed`、Frontend `46 passed`、sensitivity 通過；Browser 建房／deep refresh／`1 / 5`／Console 0 errors；未執行 AWS 寫入 | [TDD 驗證](evidence/2026-08-09-formal-entry/tdd-validation.md) |
| 2026-08-09 | 房號加入 WP-1C | 以六碼 room code＋暱稱原子性加入 Lobby；建立 Player session；補 Lobby deep-link app shell | Backend `39 passed`、Frontend `51 passed`、sensitivity 通過；Browser 小寫房號加入、`2 / 5`、deep refresh、Console 0 errors；本機 server 已停止，未執行 AWS 寫入 | [TDD 驗證](evidence/2026-08-09-formal-entry/tdd-validation.md) |
| 2026-08-10 | Session Continue 與正式路由 | 安全 session summary、首頁繼續入口、setup／lobby／play／ending mapping、Play／Ending deep link 與 HTML 404 | Backend `45 passed`、Frontend `56 passed`、兩項 sensitivity；Browser 有效／失效 session、deep routes、404、Demo 隔離與 Console 0 errors；server 已停止，未執行 AWS 寫入 | [TDD 驗證](evidence/2026-08-10-session-continue/tdd-validation.md) |
| 2026-08-10 | 三玩家完整回合 E2E | 三個隔離 origin 完成角色、開始、行動、擲骰、星火、結算與 refresh；以 TDD 修正 canonical state 未同步 deep route | Backend `45 passed`、Frontend `58 passed`、route mutation sensitivity；三端 Round `02`、點數一致、Session 隔離、`/play` 一致、Console 0 errors；未執行 AWS 寫入 | [Browser／TDD 驗證](evidence/2026-08-10-three-player-browser-e2e/validation.md) |
| 2026-08-10 | PostgreSQL restart persistence | 建立 ADR-0003、migration、PostgreSQL adapter、Memory／PostgreSQL 共用 contract 與 `DATABASE_URL` composition；修正 Demo room 重啟唯一鍵衝突 | Backend `56 passed`、Frontend `58 passed`；兩個 FastAPI application instance 還原 room 與 session；遺失 story entries mutation 正確失敗；臨時 DB 容器已移除；未執行 AWS 寫入 | [TDD 驗證](evidence/2026-08-10-postgres-persistence/tdd-validation.md) |
| 2026-08-10 | LLM recovery 與 OS process restart | 建立 retryable failure taxonomy、自動／手動 retry、`RESOLUTION_FAILED` canonical-state 保護、host-only deterministic fallback API／UI；實際啟停兩個 Uvicorn processes | Backend `66 passed`、Frontend `60 passed`；attempt-limit mutation 正確失敗；完整 room 與 session 跨 OS process restart；臨時 DB 已移除；未呼叫真實 LLM／AWS | [TDD／restart 驗證](evidence/2026-08-10-llm-recovery/tdd-validation.md) |
| 2026-08-10 | 新 AWS 帳號安全基線 | 在重新申請的 Free plan 帳號驗證每月 `US$1.00` Budget、Root MFA、Root Access Key 0、Free plan 與當月預估 `USD 0.00` | 去識別化 Console 截圖；未建立任何專題 workload | [新帳號基線](evidence/2026-08-10-new-account-baseline/validation.md) |
| 2026-08-10 | 日常人員 IAM | 建立 Console-only IAM user `ming-dev` 與 `AWSFinalProjectDevelopers` group；啟用 MFA，Access／API／SSH keys 均為 0 | 群組有 1 位成員；連接 `ReadOnlyAccess`、`IAMUserChangePassword`、`AWSBillingReadOnlyAccess`；未授予 `AdministratorAccess` 或 `PowerUserAccess` | [新帳號基線](evidence/2026-08-10-new-account-baseline/validation.md) |
| 2026-08-10 | Billing 委派唯讀 | Root 啟用 IAM user／role Billing access；`ming-dev` 可查看當月帳單與 Free plan 狀態 | 群組已連接 `AWSBillingReadOnlyAccess`；2026 年 8 月預估總計 `USD 0.00` | [群組政策](screenshots/phase0-ming-dev-group-policies.png)／[帳單證據](screenshots/phase0-ming-dev-billing-zero.png) |
| 2026-08-10 | Polling 離線／reconnect UX | 暫時性 network／`5xx` 保留 canonical 畫面並採 3／5／10 秒 bounded backoff；恢復後回 3 秒；`401/403` 停止，`409` reload | Red `4 passed, 5 failed`；Green／還原 mutation 後 Frontend `65 passed`、Backend `59 passed, 7 skipped`；未執行 AWS 寫入 | [TDD 驗證](evidence/2026-08-10-polling-offline-reconnect/tdd-validation.md) |
| 2026-08-10 | Tier 0 AWS 部署規劃 | 以 Model routing 完成服務、VPC／SG、EC2／RDS／Bedrock、IAM、TLS、成本、驗證與清理設計 | 當時為 Proposed 且未執行 AWS 寫入；所列講師、帳號、Region、credits 與 IAM 關卡後續均已完成，不是目前待辦 | [Tier 0 部署規劃](architecture/tier0-aws-deployment-plan.md) |
| 2026-08-14 | IAM bootstrap | 以 Root＋MFA 一次性建立 account protection deny 與 project-prefixed IAM delegation，並將 `PowerUserAccess` 附加至既有 developer group；隨即改回 `ming-dev` | `co-story-iam-bootstrap` `CREATE_COMPLETE`；group 6 policies；無 Access Key | [IAM／Network 部署驗證](evidence/2026-08-14-tier0-network-deployment/validation.md) |
| 2026-08-14 | Tier 0 network | 在 Tokyo 建立 `10.20.0.0/16` VPC、1 public app subnet、2 private DB subnets、IGW、route tables 與 App／DB SG；不含 compute、database、NAT 或 EIP | 19 resources `CREATE_COMPLETE`；private route local-only；DB `5432` 只接受 App SG | [IAM／Network 部署驗證](evidence/2026-08-14-tier0-network-deployment/validation.md) |
| 2026-08-14 | SG egress correction | Console 驗證發現 EC2 default allow-all egress；以 R3 TDD 與 CloudFormation localhost sink 修正 App／DB SG | Red `117bf3b`、Green `a78da19`；stack `UPDATE_COMPLETE`；final egress 截圖通過 | [IAM／Network 部署驗證](evidence/2026-08-14-tier0-network-deployment/validation.md) |
| 2026-08-15 | Tier 0 private PostgreSQL | 在 Tokyo 以 CloudFormation 建立 1 個 private Single-AZ PostgreSQL RDS 與 DB subnet group；第一次因空白 network parameters、第二次因將 Console 版本描述誤作 API engine version 而 rollback，修正後第三次成功 | `co-story-tier0-rds` `CREATE_COMPLETE`；PostgreSQL `18.3`、`db.t4g.micro`、20 GiB gp2、encrypted、Internet access gateway disabled、RDS-managed secret；credits burn 上限 `US$25/month`；最晚 2026-09-08 清理 | [RDS IaC／部署驗證](evidence/2026-08-14-tier0-rds-iac/tdd-validation.md) |
| 2026-08-15 | Tier 0 EC2＋SSM management plane | 在 Tokyo 建立 AL2023 ARM64 `t4g.micro`、8 GiB encrypted gp3、AppRole 與 instance profile；不含 Key Pair、UserData、secret 或 application deployment | `co-story-tier0-compute` `CREATE_COMPLETE`；EC2 checks passed；SSM managed node Online；Session Manager 實機驗證 `ssm-user`／`aarch64`／agent active；無 SSH／AWS CLI；credits burn 上限 `US$20/month`；最晚 2026-09-08 清理 | [EC2＋SSM IaC／部署驗證](evidence/2026-08-15-tier0-compute-iac/tdd-validation.md) |
| 2026-08-16 | Tier 0 private artifacts＋runtime secrets | 建立 private short-lived artifact bucket、application DB secret、永久 exact-secret read policy 與暫時 master-secret bootstrap policy | artifacts／runtime-secrets stacks `CREATE_COMPLETE`；bundle 由 Console 上傳並在 SSM 內以 SHA-256 驗證；無 public S3、無 secret 明文 | [Internal staging 驗證](evidence/2026-08-16-tier0-internal-staging/validation.md) |
| 2026-08-16 | Tier 0 internal staging runtime | 透過使用者逐批核准的 SSM shell 安裝 release、建立 restricted DB role、執行 migration，並啟動 FastAPI＋loopback Nginx；未開放 public Web | release `tier0-20260816-b028569`；兩個 services active；internal readiness HTTP `200`；Backend `290 passed, 8 skipped` | [Internal staging 驗證](evidence/2026-08-16-tier0-internal-staging/validation.md) |
| 2026-08-16 | EC2 service restart persistence | 由 internal API 建立專用測試房間，重啟 FastAPI service，再以同一 session 讀回相同 room／status／version；完成後刪除測試資料與 session 暫存檔 | application／Nginx active；readiness HTTP `200`；room／status／version match 全為 `true`；cleanup HTTP `204` | [Internal staging 驗證](evidence/2026-08-16-tier0-internal-staging/validation.md) |
| 2026-08-16 | Migration bootstrap access cleanup | 以 CloudFormation update 將 `EnableMigrationBootstrapAccess` 改為 `false`，只刪除 temporary master-secret read policy | Change Set 只有 1 筆 `Remove`；stack `UPDATE_COMPLETE`；application DB secret 與永久 app read policy 保留 | [Internal staging 驗證](evidence/2026-08-16-tier0-internal-staging/validation.md) |
| 2026-08-17 | Tier 0 Guardrail v1＋bounded Bedrock runtime IAM | 發布既有 Guardrail 固定 version `1`，並以 CloudFormation 只修改既有 AppRole，限定 exact Nova Lite、Guardrail v1 與 APAC guardrail profiles；未 Test／Invoke model、未啟用 logging | Change Set 只有 `AppRole Modify / Replacement=False`；compute stack `UPDATE_COMPLETE`；Policy Simulator exact v1 `Allowed`、代表性 v2 `Denied`；Access Analyzer Console pane 未顯示，記為未執行；無新增固定費 resource | [Batch 5A R3 驗證](evidence/2026-08-17-tier0-bedrock-runtime-iam/tdd-validation.md) |
| 2026-08-18 | Tier 0 least-privilege release update | 透過 Console 開啟 SSM Session，只以 Batch 6A.1 核准的兩次 exact-object S3 read 下載 archive／checksum；從已驗證 archive 取出 update installer，沿用既有 protected application DB environment，不重新取得 master secret | release `tier0-20260818-7b89e60`；checksum `OK`；application／staging Nginx active；internal readiness HTTP `200`；無新增 AWS resource、IAM 或固定費用 | [Public HTTPS R3 readiness](evidence/2026-08-18-tier0-public-https/tdd-validation.md) |
| 2026-08-18 | Tier 0 direct EC2 public HTTPS activation | 依已核准 Batch 6A，以目前 public IPv4 申請 Let's Encrypt short-lived IP certificate，切換 production runtime 與固定 IP Nginx，啟用 12 小時 renewal timer；未建立 Route 53、ACM、CloudFront、ALB、EIP 或 NAT | Application／public Nginx／renew timer active；Browser 無 certificate warning、landing page 可見、HTTP→HTTPS；`8000/8080` 不可達；bad Host `400`、bad Origin `403`、security headers present | [Public HTTPS R3 readiness](evidence/2026-08-18-tier0-public-https/tdd-validation.md) |
| 2026-08-19 | Tier 0 Batch 9A Guardrail request-tagging release | 透過 Console／SSM 以 exact 兩個 S3 objects 更新至 `tier0-20260818-a1160bc`；加入 Bedrock `guardContent`／`query` 標記與 installer `umask 0022`，未新增 resource、IAM、模型或 Guardrail 版本 | checksum `OK`；application／public Nginx／renew timer active；HTTPS `200`、`no-store`；benign 世界生成 `200`，synthetic prompt injection `503`，因無正規化 failure code 不宣稱 Guardrail smoke 通過且未重試 | [Batch 9A 與公開試玩 readiness](evidence/2026-08-19-tier0-public-trial-readiness/validation.md) |
| 2026-08-19 | Tier 0 Batch 9B 公開試玩 UX release | 以 exact 兩個 S3 objects 部署 `tier0-20260819-2de0424`；加入近端世界生成 feedback、canonical loading shell、AWS／private PostgreSQL 文案與安全 failure code logging；未呼叫模型或變更 AWS resource／IAM | checksum `OK`；services／renew timer active；HTTPS `200`、`no-store`；Landing、deep refresh、session restore、資料來源與 client validation Browser gates 通過 | [Batch 9A 與公開試玩 readiness](evidence/2026-08-19-tier0-public-trial-readiness/validation.md) |
| 2026-08-19 | Tier 0 Batch 9C Prompt Attack 代表性測試 | exactly 1 次 synthetic prompt-injection 世界生成；未重試、未變更 Guardrail／IAM／模型 | Browser 安全通用錯誤、world fields 未變；HTTP `503`、正規化 failure `SCHEMA_INVALID`，不是 Guardrail intervention，故明確記為未通過 | [Batch 9A 與公開試玩 readiness](evidence/2026-08-19-tier0-public-trial-readiness/validation.md) |
| 2026-08-19 | Tier 0 Batch 9D application-layer Prompt Injection defense | 以 exact 兩個 S3 objects 部署 `tier0-20260819-ee128da`；在 Storyteller 前拒絕明確 override／system-prompt extraction，未變更 Guardrail／IAM／模型 | services／HTTPS gate 通過；代表性注入 API `422`、剩餘次數維持 `1`、world fields 不變、Storyteller failure events `0`；零 Bedrock 呼叫 | [Batch 9A–9D 與公開試玩 readiness](evidence/2026-08-19-tier0-public-trial-readiness/validation.md) |
| 2026-08-20 | Tier 0 四玩家外部公開試玩 | 既有 production release 上由 iPhone Safari、macOS Chrome 與兩個 Windows Chrome 完成四玩家四回合、結局與刪房；只以 Console／SSM 做 bounded 唯讀證據查詢，未變更 AWS resource／IAM／release | PASS with findings；Nova Lite 6 calls、input 3,018、output 1,549、平均 latency 約 1,940 ms；EC2 CPU 峰值 1.8133%、RDS 有 client connection、HTTP `5xx=0`；發現 mobile sync、角色例外、回合選擇與刪房導頁問題 | [四玩家試玩驗證](evidence/2026-08-20-tier0-four-player-trial/validation.md)／[情境紀錄](evidence/2026-08-20-tier0-four-player-trial/trial-observations.md) |
| 2026-08-22 | Tier 0 RDS 暫停節費 | 使用者透過 Tokyo RDS Console 暫停既有 private PostgreSQL DB instance；未刪除 DB、snapshot、stack 或其他 AWS resource，Agent 未執行 AWS CLI | 使用者回報狀態 `Stopped`；DB instance hours 暫停，storage／backup 仍計費，最晚約 7 天後自動啟動；EC2 與 public HTTPS 未變 | [RDS 暫停驗證](evidence/2026-08-22-rds-temporary-stop/validation.md) |
| 2026-08-22 | Tier 0 Batch 10A stabilization release | 使用者以 Console／SSM 上傳及讀取 exact archive／checksum，部署 PR #5 tip；未新增 AWS resource、IAM 或 Bedrock 呼叫 | release `tier0-20260822-8bb6bfc`；checksum `OK`；services／renew timer active、staging inactive、HTTPS／readiness `200`；Desktop 409 與角色儲存 gate 通過，Safari 雙向同步小於 10 秒；發現 confirm `422` 後回合選擇重設 | [Batch 10A 驗證](evidence/2026-08-22-tier0-stabilization-release/validation.md) |
| 2026-08-23 | Tier 1 Batch 11A observability／operations foundation | 使用者以 MFA IAM user 在 Tokyo Console 執行兩份已審核 Change Set；建立 7 天 application Log Group、5xx Metric Filter、disabled-actions Alarm、single-instance log-write policy 與 parameter-free SSM health document；未安裝 Agent、未執行 Run Command／Bedrock | observability 四項與 `HealthCheckDocument` 均回報 `CREATE_COMPLETE`，Alarm `OK`；policy 只附加 AppRole，Access Analyzer basic validation 四類 finding 皆 `0`；log delivery、alarm trigger／recover 與 SSM 正負測試仍待後續 batch | [Batch 11A 驗證](evidence/2026-08-23-tier1-foundation-deployment/validation.md) |
| 2026-08-24 | Tier 1 Batch 11B runtime observability／IAM boundary | 使用者透過 SSM Distributor 安裝 CloudWatch Agent；首次 runtime restart race 觸發 rollback，唯讀 audit 後以 60 秒 bounded readiness wait 安全重試；啟用 allowlist JSONL collection，並以未核准 stream 執行單次 Logs 寫入負向測試；未執行 AWS CLI、S3 或 Bedrock | application active／ready、Agent active、JSONL `0640`；固定 instance stream 收到 `GET /api/v1/ready` 200 安全事件；越界 stream `PutLogEvents` 回 `AccessDenied`、未建立資源 | [Batch 11B 執行摘要](evidence/2026-08-24-tier1-runtime-observability/validation.md) |
| 2026-08-24 | Tier 1 Batch 11B bounded 5xx incident | 使用者在 Alarm `OK`／`No actions` preflight 後，對安全 JSONL append exactly one synthetic 500；未呼叫 application API、S3 或 Bedrock，未重啟服務、修改 Alarm 或重複注入 | application／Agent 前後均 active；Alarm `22:23:03` 轉 `In alarm`，在無新增 5xx 下於 `22:29:03` 自動回 `OK`；Actions 全程 `No actions` | [Batch 11B 執行摘要](evidence/2026-08-24-tier1-runtime-observability/validation.md) |
| 2026-08-25 | Tier 1 bounded AIOps zero-model release | 使用者以 Console／SSM 上傳及讀取 exact archive／checksum，部署既有 Python／Boto3 AIOps analyzer；第一次 tar member pipe 檢查 false negative 於安裝前停止，修正檢查後完成部署；未新增 AWS resource、IAM 或 Bedrock 呼叫 | release `tier1-20260824-59f5458`；checksum `OK`；application／CloudWatch Agent／public edge active；safe log 最近 200 行 accepted `200`、discarded `0`；zero-model gate exit `0` | [AIOps Agent 驗證](evidence/2026-08-24-tier1-aiops-agent/validation.md) |
| 2026-08-25 | Tier 1 exactly-one Nova Lite AIOps gate | 使用者另行核准後，以 SSM Session 執行一次 bounded AIOps entrypoint；先建立不可重跑 marker，adapter retries `0`，不具自動修復能力 | 模型輸出未通過固定契約，安全回 `SCHEMA_INVALID`／exit `3`；application／CloudWatch Agent／public edge 前後 active；未執行建議 action、未重試 | [AIOps Agent 驗證](evidence/2026-08-24-tier1-aiops-agent/validation.md) |
| 2026-08-25 | Tier 1 forced-tool AIOps replacement | 使用者以 Console／SSM 部署 exact replacement archive／checksum；保留舊 exactly-one marker，以 fake Converse client 驗證 forced output-tool contract，未呼叫 Bedrock | release `tier1-20260825-38296e7`；checksum `OK`；application／CloudWatch Agent／public edge active；safe log 200 行 accepted `199`、discarded `1`；zero-model gate exit `0` | [AIOps Agent 驗證](evidence/2026-08-24-tier1-aiops-agent/validation.md) |
| 2026-08-25 | Tier 1 forced-tool Nova Lite healthy-state decision | 使用者另行核准 exactly-one invocation；新不可重跑 marker、retries `0`，模型只可提交 output-only report，不具 recovery tool | 固定 schema 成功；5xx `0`、建議 `NO_ACTION`、人工批准 required；使用者明確批准 `NO_ACTION`，三個 services 前後 active，未執行任何變更 | [AIOps Agent 驗證](evidence/2026-08-24-tier1-aiops-agent/validation.md) |
| 2026-08-25 | Tier 1 bounded AIOps incident response | exactly one synthetic 500 觸發既有 disabled-actions Alarm 後自動回 `OK`；使用者另行核准 forced-tool Nova call，拒絕缺乏 DB 證據的 `CHECK_DATABASE`，改批准既有唯讀 SSM health document | analysis schema成功、三個 services前後 active；單一 target Run Command `Success`／response `0`，`service=active`、`live=200`、`ready=200`、Error `0`；未 restart、讀 DB secret 或重試模型 | [AIOps Agent 驗證](evidence/2026-08-24-tier1-aiops-agent/validation.md) |
| 2026-08-25 | Tier 1 observability completion | 以 Change Set 擴充固定 system Log Group、HTTP／Storyteller metric filters、Dashboard 與限縮 namespace 的 system metric IAM；第一版因 Managed Policy replacement gate 停止，保留 Description 後以 `Replacement=False` 更新。部署 sanitized system health timer、memory／root disk metrics 與 Bedrock usage telemetry；不收 raw journal／auth log | active release `tier1-20260825-4a51e0e`；system JSONL delivery、memory／disk、HTTP latency、Nova Lite input `206`／output `465`／latency `2,823 ms`／估計 `US$0.00012396` 全部可見；exactly-one zero baseline 顯示 retry／fallback 均 `0`，未呼叫 Bedrock 或 recovery action | [Tier 1 完成驗證](evidence/2026-08-25-tier1-completion/validation.md) |
| 2026-08-26 | Tier 3 Batch T3A delivery control plane | 使用者在 Tokyo Console 執行已審核 Change Set，建立 immutable／scan-on-push ECR、main-only GitHub OIDC deploy role、AppRole pull-only policy與固定 instance／document 的 SSM release document；沒有 image push、SSM command、Docker bootstrap 或 production deployment | 五項資源均 `CREATE_COMPLETE`；OIDC `aud`／exact `sub` 無 wildcard、deploy role boundary、ECR pull／push resource scope、ECR lifecycle、SSM schema／parameter pattern均通過；Policy Simulator 顯示 `PassRole`／delete／StartSession／跨 repository deny，指定 repository `PutImage` allow。ECR 保持空，active release 未變 | [Batch T3A control plane 驗證](evidence/2026-08-26-tier3-control-plane/validation.md) |
| 2026-08-27 | Tier 3 Batch T3B 首次 production workflow（fail closed） | 使用者先完成 release／legacy rollback Documents Change Set、bounded Docker bootstrap、GitHub production reviewer／main-only gate與四項repository variables，再核准 exact main `0add833c…` 的 `legacy-bootstrap` workflow；OIDC、ARM64 build與immutable ECR push成功 | Trivy v0.70.0在amd64 runner未明確選擇`linux/arm64`，無法解析ARM64-only image而失敗；SSM release step明確`skipped`，未執行migration、container部署或流量切換，active release維持`tier1-20260825-4a51e0e`。禁止re-run舊SHA，須先以TDD修正並對新SHA重新核准 | [T3B首次run驗證](evidence/2026-08-27-tier3-production-release/validation.md) |
| 2026-08-27 | Tier 3 Batch T3B 第二次 production workflow（fail closed） | 使用者核准 exact main `d81e4d7…` 的`legacy-bootstrap`；OIDC、ARM64 build／immutable push與exact-digest Trivy均通過，SSM command送達單一target | Migration因container未掛載host RDS CA而回`migration_failed`，發生在candidate與任何unit／state mutation前；唯讀postflight確認legacy active、live／ready `200`，沒有release env、transition state、backup、stable assets或container殘留。GitHub raw instance variable另含前置控制空白，waiter回validation error；禁止re-run同SHA | [T3B production驗證](evidence/2026-08-27-tier3-production-release/validation.md) |
| 2026-08-27 | Tier 3 Batch T3B 第三次 production workflow（fail closed） | 使用者先將release Document更新至version 3並修正canonical instance variable，再核准 exact main `2fbe3c8…` 的`legacy-bootstrap`；OIDC、ARM64 build／immutable push、exact-digest Trivy、RDS CA preflight與migration均通過，SSM command送達單一target | Candidate因container UID `10001`無法寫入host `co-story` UID持有的安全JSONL而未在`:8001`啟動，回`target_candidate_unhealthy`；失敗發生於任何unit／state mutation前。唯讀postflight確認legacy application／public edge active、container service inactive、health Document `live=200`／`ready=200`，沒有release env、transition state、backup、stable assets或container殘留。禁止re-run同SHA | [T3B production驗證](evidence/2026-08-27-tier3-production-release/validation.md) |
| 2026-08-27 | Tier 3 Batch T3B 第四次 production workflow（首次container transition成功） | 使用者核准 exact main `1681736c…` 的`legacy-bootstrap`；run `33045168887`通過OIDC、ARM64 build／immutable push、exact-digest Trivy、SSM migration／candidate／target與public edge gate | Production成功切換container runtime並保存legacy rollback state；唯讀postflight確認服務與live／ready正常、digest與runtime identity吻合、log可寫。Docker內建HEALTHCHECK因literal Host header顯示`unhealthy`，實際allowlisted probe為`200`，故未rollback或restart並改採test-first修正 | [T3B production驗證](evidence/2026-08-27-tier3-production-release/validation.md) |
| 2026-08-27 | Tier 3 HEALTHCHECK `digest-release`與完成 gate | PR #21以strict TDD改由既有runtime allowlist選取health Host；使用者核准 exact main `e82c683…`、previous digest `sha256:bab8a1…`的`digest-release`，run `33048585714`完整成功 | Active digest更新為`sha256:32bee84…`；application、public edge、CloudWatch Agent與system timer active，Docker `healthy`／failing streak `0`，state `container-active`、state／release env `7／3`行、digest／identity／log均吻合、candidate `0`、live／ready `200`。Tier 3 gate完成 | [T3B production驗證](evidence/2026-08-27-tier3-production-release/validation.md) |
| 2026-08-28 | Tier 2 migration bridge production deployment | 使用者先將bounded `ContainerReleaseDocument`更新至version 4，再核准exact main `8ab5fe0…`、previous digest `sha256:32bee84…`的`migration-bridge`。前兩次target activation失敗均fail closed並回復previous runtime；PR #29／#30以strict TDD修正後，run `33145778589`完整通過approval、OIDC、ARM64 build／push、Trivy與SSM | SSM `Status=Success`／response `0`，回`container_release=verified mode=migration-bridge`；active digest更新為`sha256:b9272ee…`，沒有執行`002`／`003`／`004`或啟用async Worker。唯讀postflight確認marker／digest／sync mode、Docker `healthy`、四項services及live／ready全部通過；previous digest與legacy rollback資產保留 | [Migration bridge驗證](evidence/2026-08-28-tier2-migration-bridge/validation.md) |
| 2026-08-28 | Tier 2 schema activation production deployment | 首次activation因舊stable driver在preflight誤刪marker而fail closed；PR #32／#33以strict TDD修正marker生命週期及exact target-driver routing，CloudFormation只更新`ContainerReleaseDocument.Content`至version 5。使用者完成bounded marker recovery後，核准exact main `2472e49…`、previous bridge digest `sha256:b9272ee…`的run `33170836289` | SSM `Status=Success`／response `0`，回`container_release=verified mode=schema-activation`；active digest更新為`sha256:6d0d732…`，inventory精確為`001`／`002`／`003`／`004`。Postflight確認marker清除、state／release env `7／3`行、asset checksum、sync runtime、Docker healthy、四項services及live／ready全部通過；async Worker尚未啟用 | [Migration bridge驗證](evidence/2026-08-28-tier2-migration-bridge/validation.md) |
| 2026-08-29 | Tier 2 private Worker foundation deployment | 首次執行因SQS不接受單一TLS policy statement含兩個Queue resources而rollback；PR #36以strict TDD拆成兩個單resource statements。使用者重新建立20-Add Change Set並在USD 35上限、2026-09-08清理日及foundation-only邊界下執行 | `co-story-tier2-worker-foundation` 20／20 resources `CREATE_COMPLETE`；兩台private`t4g.micro`／8 GiB encrypted gp3、SSM online、Docker active且無container；Queues為空、DLQ alarm `OK`／actions disabled；SG與Worker／Web IAM正負控制通過。Production仍為`sync`，未部署Worker image、傳送message或呼叫Bedrock | [Worker foundation驗證](evidence/2026-08-28-tier2-aws-worker-foundation/validation.md) |
| 2026-08-29 | Tier 2 private Worker runtime first deployment | PR #38完成SQS consumer／heartbeat／secret bootstrap與hardened unit；PR #39新增Worker-only artifact workflow。Production approval後run `33233803509`由exact main `0ea4b125…` build／push ARM64 image、Trivy掃描exact digest並保存manifest；使用者再以bounded SSM Run Command部署同一digest至兩台private Worker | Digest `sha256:ede0f8e…`；SSM精確`2/2 Success`、兩台response `0`，兩個不同CloudWatch log streams；主Queue／DLQ的available／in-flight皆為`0`。Web仍為`sync`，未傳送message、未呼叫Bedrock、未修改IAM／CloudFormation resource inventory | [Worker runtime部署驗證](evidence/2026-08-29-tier2-worker-runtime-deployment/validation.md) |
| 2026-08-29 | Tier 2 Worker replacement-safe bootstrap | 三次rolling update均因bootstrap缺陷fail closed並rollback；新增phase診斷後證實AL2023預裝`curl-minimal`與完整`curl`套件衝突。PR #44以strict TDD只安裝Docker並驗證既有curl binary；使用者在相同成本／清理／sync envelope內執行最終Change Set | Stack、Launch Template與ASG均`UPDATE_COMPLETE`，ASG Desired／In service `2／2`；success signal綁定exact image、service active、container running與restart `0`。Resource仍精確20，未新增IAM、NAT、compute、Queue，未送message、呼叫Bedrock或啟用async | [Worker replacement bootstrap驗證](evidence/2026-08-29-tier2-worker-replacement-bootstrap/validation.md) |
| 2026-08-29 | Tier 2 `005` migration bridge | 使用者核准exact main `4435fdb…`與previous digest `sha256:6d0d732…`的`migration-bridge`；run `33241665137`通過production approval、OIDC、ARM64 build／immutable push、exact-digest Trivy與bounded SSM | SSM `Status=Success`／response `0`；active bridge digest為`sha256:c0efe0f…`。此mode未執行migration，schema仍為`001`–`004`、Web仍為`sync`；未安裝／啟用publisher、未送SQS或呼叫Bedrock | [Migration bridge驗證](evidence/2026-08-28-tier2-migration-bridge/validation.md) |
| 2026-08-29 | Tier 2 `005` schema activation首次嘗試（fail closed） | 使用者核准exact main `61a736a…`、previous bridge digest `sha256:c0efe0f…`的run `33242226396`；approval、ARM64 build／push、digest fence與Trivy通過 | Target digest `sha256:811faece…`；SSM preflight通過後，`005`因不存在的`jsonb_object_length(jsonb)`回`migration_failed`／response `2`。Release在image切換前停止，Web維持`sync`、publisher未啟用；禁止rerun舊run，改以strict TDD修正後建立新exact image | [`005` activation驗證](evidence/2026-08-29-tier2-schema-activation-release/validation.md) |
| 2026-08-29 | Tier 2 `005` schema activation完成 | PR #50修正JSONB CHECK並通過四項CI；使用者核准exact main `ae2666a…`、previous bridge digest `sha256:c0efe0f…`的全新run `33243455252` | Target digest `sha256:abd0f942…`；SSM success／response `0`並回`container_release=verified mode=schema-activation`。Postflight確認inventory精確`001`–`005`、Web `sync`、bridge marker清除、publisher unit／env／container均不存在；未送SQS或呼叫Bedrock | [`005` activation驗證](evidence/2026-08-29-tier2-schema-activation-release/validation.md) |
| 2026-08-29 | Tier 2 publisher disabled-only unit安裝 | PR #52修正systemd `static` state判斷並通過四項CI；run `33246093420`將exact main `9337026…`以`digest-release`部署為`sha256:af120cbb…`。使用者再以bounded SSM只從active exact image安裝unit | Installer回`installed:disabled`；postflight確認unit `static`、service `inactive`、runtime env／publisher container absent、Web `sync`。未enable／start／restart、未送SQS或呼叫Bedrock，無IAM／AWS resource新增 | [Publisher service驗證](evidence/2026-08-29-tier2-publisher-service/validation.md) |
| 2026-08-29 | Tier 2 publisher activation | 使用者核准建立最小publisher runtime env並人工啟動既有static unit；Web固定`sync`且不建立test job。首次指令因誤用source asset service名稱而在mutation前停止，修正為production安裝名稱後成功 | Postflight回`publisher_activation=verified unit=static service=active container=running outbox_total=0 web=sync`；active exact digest仍為`sha256:af120cbb…`。未enable service、未建立test job、未切換Web async或新增AWS resource；成本上限USD 35與2026-09-08清理日不變 | [Publisher service驗證](evidence/2026-08-29-tier2-publisher-service/validation.md) |
| 2026-08-29 | Tier 2 typed JSONB producer release與首次exactly-one測試 | PR #55以psycopg typed `Jsonb`修正outbox payload；run `33253308679`綁定exact main `b4b6e28…`完成ARM64 build、scan及digest release，Web與publisher切至`sha256:23357e3…`。使用者另行核准建立exactly-one test job、單次SQS message與Bedrock invocation | Setup回`typed_jsonb=true`，job完成三次bounded attempts且dispatch／completion皆為true，但room以`RESOLUTION_FAILED／INVALID_MODEL`結束。Marker已清除，Web仍`sync`、publisher active，主Queue／DLQ available與in-flight四項皆為`0`；未重跑測試 | [Producer JSONB修正](evidence/2026-08-29-tier2-producer-jsonb-fix/validation.md) |
| 2026-08-29 | Tier 2 Nova Lite相容Worker rollout | PR #56以strict TDD只對exact Nova Lite v1轉換outgoing tool schema；run `33257141550`綁定exact main `98ded43…`完成ARM64 immutable image、exact-digest Trivy與manifest。使用者核准兩台Worker由`sha256:ede0f8e…`逐台更新 | 新digest `sha256:94ff5d2c…`；兩台均回preflight compatible與release verified，service active、container running、restart `0`、mode async。其後兩台均完成registry logout並確認credential absent；Web維持`sync`，未建立新test job、未送SQS或呼叫Bedrock，故live模型修正仍待驗證 | [Nova Lite相容性驗證](evidence/2026-08-29-tier2-nova-tool-schema-compatibility/validation.md) |
| 2026-08-30 | Tier 2 safe diagnostics Worker rollout與successful exactly-one AWS E2E | PR #58以strict TDD加入固定allowlist schema診斷；run `33296013600`綁定exact main `81bf54a…`完成ARM64 immutable push、exact-digest Trivy及manifest。兩台Worker以bounded SSM更新至`sha256:2d5d586…`後，使用者另行核准一個test job、單次SQS dispatch與至多一次Bedrock invocation | 兩台Worker均active／running／restart `0`／async且credential absent。Exactly-one為dispatch `1`、attempt `3/3`、result `applied`、Room `COLLECTING_ACTIONS`；marker清除，publisher active、Web維持`sync`，主Queue／DLQ available與in-flight四項皆為`0`。玩家async尚未啟用 | [Safe schema diagnostics驗證](evidence/2026-08-30-tier2-safe-schema-diagnostics/validation.md) |
| 2026-08-31 | Tier 2 production Web async activation與玩家E2E完成 | PR #59–#63以strict TDD建立candidate-first、精確failure diagnostics與bounded startup polling；exact main `bf7de1f…`的activation回`sync → async` verified。手動世界建立三玩家測試房間；首次單一job以一次dispatch／一次invocation回`TRANSIENT_SERVICE_ERROR`，Web立即rollback至`sync`且所有終態清空。使用者另行核准一次人工bounded retry，重新activation並對新job固定`retry_seed=2` | Retry精確dispatch `1`、attempt `3/3`、invocation budget `1`、result `applied`；Browser顯示Round 02與新故事，Room `COLLECTING_ACTIONS`。最終Web `async`、Publisher與兩台Worker active，主Queue／DLQ五項均`0`、DLQ alarm `OK`／`No actions`。保留單一測試房間至2026-09-08；stale pending feedback列為UI residual | [Web async activation驗證](evidence/2026-08-31-tier2-web-async-activation/validation.md) |
| 2026-08-31 | Tier 2 Web UI patch production release與async corrective | PR #65修正terminal stale feedback並移除未接contract的建立新房間控制；使用者核准exact main `58fc124…`、previous digest `sha256:23357e3…`的`digest-release`，active Web更新為`sha256:926f19e…`。Release後發現runtime mode退回`sync`；第一次bounded corrective因script checksum mismatch在mutation前停止，第二次精確payload完成`sync → async` | Postflight確認application／public edge／publisher active、container healthy／restart `0`、active digest與state一致、installed／stable unit各精確一個`async`、candidate與residual artifacts均為`0`，internal／public live／ready皆為`200`。Publisher與兩台Worker digest未變；未建立story job或呼叫Bedrock。PR #69已修正未來SSM Document的exact target-driver handoff，但AWS Document尚待獨立Change Set更新 | [Web UI release驗證](evidence/2026-08-31-tier2-web-ui-release/validation.md)／[Tier 3 release corrective](evidence/2026-08-31-tier3-production-release/validation.md) |
| 2026-08-31 | Support Agent Phase A production release | PR #66／#68整合Web與API，PR #69修正exact target-driver handoff；使用者先將`ContainerReleaseDocument`更新至version 6，再核准exact main `1f448bf…`的`digest-release`。Run `33385137007`通過production approval、OIDC、ARM64 build／immutable push、exact-digest Trivy與bounded SSM | Active Web更新至`sha256:e0bdfc8…`並維持`async`；application／public edge／CloudWatch Agent／timer／publisher active，container healthy／restart `0`。Browser驗證supported citation、unsupported不猜測與Player `local_draft_only`人工確認草稿；rules requests均`200`，無外部submit或Bedrock呼叫 | [Support Agent integration驗證](evidence/2026-08-31-support-agent-integration/validation.md) |
| 2026-08-31 | Support Agent CSP corrective production release | PR #70以strict TDD移除inline script與Google Fonts，改由既有module處理`file://`提示並使用系統CJK字型，不修改`default-src 'self'`。使用者核准exact main `372a2cb…`、previous digest `sha256:e0bdfc8…`；run `33398071307`完整通過approval、OIDC、ARM64 image、digest fence、Trivy、SSM與metrics artifact | Active Web更新至`sha256:f9cc0e6…`；state／release env `7／3`、三方digest一致、runtime `async`、container healthy／restart `0`、publisher digest保留。Browser hard reload確認inline CSP error、Google Fonts request與CSP error均不存在，rules lookup `200`且render正常 | [CSP corrective驗證](evidence/2026-08-31-support-csp-corrective/validation.md) |
| 2026-09-01 | UI terminal refresh與像素Support Widget production release | UI／Widget兩分支完成整合QA後合併至main；使用者核准exact main `1297a6a…`、previous digest `sha256:f9cc0e6…`的`digest-release`。CI run `33493821544`與release run `33494151458`通過Frontend／Backend、ARM64 image、digest fence、Trivy、bounded SSM與metrics artifact | Active Web更新為`sha256:5a10597…`並維持`async`；Publisher與兩台Worker不變。Production Browser確認`Release v1.1.0`、新品牌SVG、像素Widget、Esc focus return，390px無nav／composer重疊與水平溢位，console無error／warning | [UI／Widget production驗證](evidence/2026-09-01-ui-support-production-release/validation.md) |
| 2026-09-01 | Direct IP憑證事故與bounded recovery | 公開UI smoke發現既有憑證過期；timer雖active，但ACME token因`/var/lib/co-story`的`0750`父目錄阻擋Nginx worker而回`404`，renewal自8月28日起失敗。使用者核准後只加入`user:nginx:--x` ACL，未放寬list／read／write，也未變更AWS資源、IAM或Web image | Loopback與外部challenge probe精確`200`；同一renewal unit `Result=success`／exit `0`、Nginx reload成功，新憑證有效至2026-09-08；外部strict TLS首頁／live／ready均`200`。下一次timer自動renew與repo防回歸尚待收斂 | [UI／Widget production驗證](evidence/2026-09-01-ui-support-production-release/validation.md) |
| 2026-09-02 | 寵物規則助手 production release | PR #71整合寵物UI與deterministic rules retrieval、PR #72收斂文件；使用者核准exact main `4db923f…`、previous digest `sha256:5a10597…`的`digest-release`。Main CI run `33577941894`首次僅因Docker Hub拉取BuildKit timeout而在build／scan前停止，failed jobs rerun後全綠；release run `33578331749`通過approval、OIDC、ARM64 image、digest fence、Trivy、bounded SSM與metrics artifact | Active Web更新為`sha256:14d8e0f…`並維持`async`；Publisher、兩台Worker及migration `001`–`005`不變。Production Browser驗證390／768／1440、中文片語、六個主題、citation、unsupported不猜測與`/support`退場；strict TLS首頁／live／ready皆`200`。無Bedrock、RAG、MCP、external submit或新story job | [寵物規則助手 production驗證](evidence/2026-09-02-pet-rules-production-release/validation.md) |

## AWS Budget Alarm

| 項目 | 狀態 |
| --- | --- |
| 是否已建立 | 已驗證，運作狀態正常 |
| 預算金額 | 每月 `US$1.00` |
| 目前支出 | `US$0.00`（2026-08-10 新帳號驗證） |
| 通知設定 | 提醒閾值已確認；Email 位址未保存於證據 |
| 截圖 | [phase0-new-account-budget.png](screenshots/phase0-new-account-budget.png) |

## 2026-08-10：新 AWS 帳號安全與 IAM 基線

- 本節是目前後續部署候選帳號；下方 2026-08-06–07 的 Organization／Identity Center 紀錄只屬舊帳號歷史。
- Billing Console 顯示 Free plan；當月預估 `USD 0.00`，每月 `US$1.00` Budget 正常。
- Root 與 `ming-dev` 均已啟用 MFA；Root 與 `ming-dev` 沒有長期 Access Key。
- `ming-dev` 是 Console-only 日常人員身分，位於 `AWSFinalProjectDevelopers`；2026-08-14 已附加 `PowerUserAccess` 與專題前綴 IAM delegation，並以 account protection explicit deny 限制高風險帳號操作。
- Root 只用於一次性 IAM bootstrap，完成後已登出；一般專題資源由 MFA 的 `ming-dev` 操作，仍無長期 Access Key。
- 2026-08-13 已補驗證 Credits、Organizations 缺席與 Tokyo Region；2026-08-14 已建立 IAM bootstrap 與 Tier 0 network，詳見最新變更紀錄。

證據：[2026-08-10 新帳號安全與成本基線](evidence/2026-08-10-new-account-baseline/validation.md)

## 歷史舊帳號：2026-08-06–07 Agent Skill、Organizations 與 IAM Identity Center

> 本節帳號已因建立 AWS Organization 永久升級 Paid plan；不得把它的 Organization、Identity Center、principal、Budget 或 credits 狀態套用到 2026-08-10 新帳號。

| 項目 | 狀態 | 證據／下一步 |
| --- | --- | --- |
| 專題 Agent Skill | 已建立並通過結構驗證 | [Skill 驗證](evidence/2026-08-06-skill-and-iam/skill-validation.md) |
| AWS principal／account／Region | Root user；Organizations management account；Tokyo `ap-northeast-1` | 帳號 ID 未保存；[P0-1 證據](evidence/2026-08-07-p0-1-account-security/inventory-summary.md) |
| IAM Identity Center | 舊帳號曾在 Tokyo 啟用單一區域 organization instance | [舊帳號啟用結果](evidence/2026-08-07-identity-center/enable-result.md)；相關截圖已清除 |
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
