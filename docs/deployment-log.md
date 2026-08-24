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
| 2026-08-10 | Tier 0 AWS 部署規劃 | 以 Model routing 完成服務、VPC／SG、EC2／RDS／Bedrock、IAM、TLS、成本、驗證與清理設計 | Proposed；尚待講師、帳號、Region、credits、估價與 IAM 關卡；未執行 AWS 寫入 | [Tier 0 部署規劃](architecture/tier0-aws-deployment-plan.md) |
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
| 2026-08-24 | Tier 1 Batch 11B runtime observability／IAM boundary | 使用者透過 SSM Distributor 安裝 CloudWatch Agent；首次 runtime restart race 觸發 rollback，唯讀 audit 後以 60 秒 bounded readiness wait 安全重試；啟用 allowlist JSONL collection，並以未核准 stream 執行單次 Logs 寫入負向測試；未執行 AWS CLI、S3 或 Bedrock | application active／ready、Agent active、JSONL `0640`；固定 instance stream 收到 `GET /api/v1/ready` 200 安全事件；越界 stream `PutLogEvents` 回 `AccessDenied`、未建立資源。5xx alarm trigger／recover 待後續 | [Batch 11B 執行摘要](evidence/2026-08-24-tier1-runtime-observability/validation.md) |

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
