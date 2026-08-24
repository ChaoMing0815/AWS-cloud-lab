# CURRENT：目前工作交接

- 更新日期：2026-08-24
- 近期目標：完整交付 Tier 0–2；若 2026-09-01 前 Tier 2 AWS E2E 穩定通過，挑戰以 Docker、ECR、GitHub OIDC 與 SSM 完成 Tier 3 自動部署垂直切片。目前先完成 Tier 1 CloudWatch／SSM／AIOps incident。
- Branch：`codex/tier1-runtime-observability`，由 PR #7 merge commit `9dc2350` 建立；Tier 1 SSM health-check 第一版 Red `f854723`／Green `3dd8a84`，versioned route 修正 Red `dcd8efd`／Green `529d223`；Batch 11A evidence commits `35aa801`、`94e4358`。
- 本機功能 checkpoint：公開試玩 UX／安全失敗記錄 `d2b76ba`；canonical route loading shell `f9d4155`；明確 Prompt Injection 前置拒絕 `6f872b2`；widow／orphan 排版規則 `18fcd21`；首頁公開試玩安全提示 `62b4e02`。
- Regression：Backend `330 passed, 8 skipped`（2026-08-24，versioned health route R3 gate）；Frontend `94 passed`（2026-08-23，最近一次前端 gate）。
- AWS active release：`tier0-20260822-c5c1541`。
- 操作邊界：Console-first；未經新的 bounded batch 核准不得執行 AWS CLI。使用者操作 AWS Console／SSM，Agent 只提供單一可驗證步驟。

## Current

- Tier 0 AWS 基礎已完成：Tokyo VPC、公網 EC2＋SSM、private PostgreSQL RDS、private S3 artifacts、runtime secret、Guardrail v1 與 bounded Bedrock runtime IAM；無 NAT、EIP、SSH、ALB、CloudFront、Route 53 或自有網域。
- 公開 HTTPS 已啟用：Let's Encrypt short-lived IP certificate、public Nginx 與 renewal timer active；HTTP→HTTPS、bad Host／Origin、security headers、public `8000/8080` 不可達均已驗證。
- Batch 8A 已完成 AWS 三玩家單回合 smoke：三個 Browser sessions 建立角色、同步 action、擲骰、星火決策與房主結算；進入 Round 2，進度 `4（13%）`、危機 `2（7%）`，三端 refresh 後由 private RDS 完整讀回。
- PR #3 已合併至 `main`；merge commit `3c5db99`。Batch 9A 隨後部署 `tier0-20260818-a1160bc`，exact S3 objects `2`、checksum `OK`，application／public Nginx／renew timer active、staging inactive、HTTPS readiness `200`、首頁 `Cache-Control: no-store`。
- Batch 9A 只允許兩次 bounded 世界生成呼叫，均已用完：benign request 回 `200` 並產生完整世界草稿；synthetic prompt-injection request 回 `503`。`503` 只能證明應用失敗，不能證明 Guardrail Prompt Attack filter 介入，故目前不得宣稱 Prompt Attack smoke 通過，也不得在新核准前重試。
- `a1160bc` 已包含 Bedrock `guardContent`／`query` 標記與 installer `umask 0022`，但當時 runtime 沒有安全、正規化的 storyteller failure log；因此無法由既有 log 判定 `503` 是 `CONTENT_REJECTED`、schema invalid 或其他 provider failure。
- Batch 9B 已部署 `tier0-20260819-2de0424`：exact S3 objects `2`、checksum `OK`；application／public Nginx／renew timer active、staging inactive、HTTPS readiness `200`、首頁 `Cache-Control: no-store`。Browser 已驗證 AWS runtime 文案、private PostgreSQL 標示、canonical loading shell、session restore 與近端 validation error；未呼叫 Bedrock。
- 該版本的本機 Red commits 為 `66ee7b5`、`8c9bde0`、`816b817`；Green commits 為 `d2b76ba`、`f9d4155`。世界生成按鈕旁顯示 loading／安全錯誤、關鍵字接受 `、`／`，`／`,`、範例文字泛用化，後端只記 allowlist failure code，不記 prompt、room、player、AWS 原始錯誤或 secret。
- Batch 9C exactly 1 次 synthetic prompt-injection 世界生成已完成：Browser 顯示安全的「世界生成暫時無法完成」、world fields 未變、生成剩餘次數由 `2` 變 `1`；正規化 log 為 `SCHEMA_INVALID`、HTTP `503`。這不是 `CONTENT_REJECTED` 或 Guardrail intervention，證明既有 Prompt Attack filter 對代表性測試不足以單獨依賴；禁止重試。
- Application-layer 明確注入前置拒絕已依嚴格 TDD 完成並部署：Red `a3f12a8`、Green `6f872b2`，active release `tier0-20260819-ee128da`。Batch 9D Browser 驗證英文 override＋system-prompt extraction 在 Storyteller 前回安全 `422`，生成剩餘次數維持 `1`、world fields 不變、`STORYTELLER_FAILURE_LOGS=0`；普通「忽略風雨」故事語句仍通過。此 bounded detector 只是 defense-in-depth，不宣稱能偵測所有 Prompt Injection。
- 同學／友人試玩已限縮為 AWS 外部 E2E 驗證：客觀記錄 HTTPS、三玩家同步、Bedrock 敘事、refresh persistence、錯誤與完成時間；非阻斷性的 UI／UX 回饋不在本輪範圍。操作、停止條件與去識別化證據規則見 `docs/qa/public-trial-guide.md`。
- 公開試玩前的 UI 收尾已依 TDD 完成：標題與段落使用 responsive `balance`／`pretty` wrapping，列印樣式避免單行跨頁；首頁移除硬編換行並加入「使用暱稱、勿輸入個資／機密」提示。Red commits 為 `a3337b0`、`bf8b193`；Green commits 為 `18fcd21`、`62b4e02`，目前已包含於 Batch 10A active release。
- 2026-08-20 完成 Tier 0 四玩家、四回合外部公開試玩：iPhone 12 Safari 房主、macOS Chrome 與兩個 Windows Chrome 玩家均完成加入、角色、四回合、Bedrock 敘事、結局與刪房。AWS E2E 判定為 **PASS with findings**。
- Bedrock CloudWatch 在 22:10–23:00 顯示 Nova Lite `Invocations=6`、input tokens `3,018`、output tokens `1,549`，六次呼叫與世界生成、四回合敘事及結局一致；加權平均 latency 約 `1,940 ms`。EC2 CPU 峰值約 `1.8133%`，RDS `DatabaseConnections` 有非零 client connection。
- Sanitized access log：`200 × 2,671`、`201 × 5`、`204 × 1`、`404 × 317`、`409 × 30`、`5xx × 0`。房間於 22:53:22 成功刪除；317 次 current-room `404` 全部從刪除後 24 秒才開始，確認是舊分頁未停止 polling。
- 公開試玩發現：iPhone Safari 需頻繁手動更新、世界生成前回合數會回預設值、角色儲存後曾顯示原始 JavaScript exception、刪房後各頁未立即導頁，以及回合敘事偏向逐句整合而非深入演繹。前三類 state／error 與刪房 lifecycle 是正式修正候選；敘事品質列為 post-MVP Prompt 優化。
- 8/20 backend metrics／sanitized logs 已入 `docs/evidence/2026-08-20-tier0-four-player-trial/`。六張受測者原圖含 public IP、暱稱、通知或 Browser 資訊，未直接入庫；先以去識別化文字紀錄，報告圖待裁切／遮罩。
- Batch 8A 後 Cost Explorer 的 Total、Bedrock、EC2、RDS 與其他服務當時均顯示 `0`；帳務可能延遲，不能解讀為永久零成本。Credits 尚餘 `US$137.40`，最近到期日 2027-09-08。
- 第一次進度書面報告初稿已產出至 `docs/reports/2026-08-24-first-progress-report.docx`。內容已納入 Tier 0–5 選題思路、商業價值、前後端與 AWS 架構、Web／DB 分離、公私 subnet、重啟後 RDS persistence、CloudFormation、成本管控、Prompt Injection 防護邊界、實際遊玩畫面與後續演進；中文字體、標題尺寸、段落間距及單行跨頁已調整。
- 第一次進度簡報已產出至 `docs/presentations/2026-08-24-first-progress-presentation.pptx`，共 13 頁並附逐頁繁體中文講稿。投影片以簡短文字、實際遊玩畫面與圖解呈現，另加入前端／後端責任及各自與 AWS 的串接方式；架構連線改用直角路徑，避免斜線穿越區塊。已通過投影片 overflow、逐頁視覺與 PowerPoint 壓縮檔完整性檢查。
- 第一次進度報告、簡報與三張可重用架構圖已在 `bf12650` commit 並 push；Office 檔經壓縮結構與敏感字串 pre-push audit。報告產生／修復腳本因含本機限定路徑未入庫，已保留在 `/private/tmp/co-story-report-scripts-20260821`；`.gitignore` 已排除 `~$*` Office 鎖定檔。
- GitHub CI foundation 已依嚴格 TDD 完成本機 Red `832d6bf` 與 Green `a8763df`：`.github/workflows/ci.yml` 在 pull request 與 `main` push 執行獨立 Backend／Frontend jobs，固定 Python `3.13`、Node `24` 與唯讀 `contents: read`；明確不授予 OIDC、AWS、ECR 或部署能力。Contract targeted tests `2 passed`，本機 Backend `313 passed, 8 skipped`、Frontend `85 passed`。兩個 commits 已 push；GitHub Actions run `32478705788` 實際通過，`backend-tests` 約 25 秒、`frontend-tests` 約 9 秒。PR checks 已成立，branch protection required checks 尚未設定。
- 角色儲存原始 JavaScript exception 已完成 R2 TDD：Red `6d3c8fe` 精確證明未知 `TypeError.message` 會外露；Green `49aa5dc` 只允許 `ApiError`／`DomainError` 的 `publicMessage` 顯示，未知錯誤改為「角色儲存失敗，請重新整理後再試。」並保留輸入、canonical room、解除 busy。Targeted `3 passed`、Frontend `88 passed`，代表性 sensitivity 可抓回直接顯示原文的 mutation；GitHub Actions run `32496325155` 的 `backend-tests` 與 `frontend-tests` 均通過。Batch 10A 已部署，Desktop 角色儲存／改名成功且 Console error `0`。驗證見 `docs/evidence/2026-08-21-character-error-safety/validation.md` 與 `docs/evidence/2026-08-22-tier0-stabilization-release/validation.md`。
- 刪房後舊分頁 polling lifecycle 已完成 R2 TDD：Red `a2b192d` 證明 `404 ROOM_NOT_FOUND` 仍會向外拋出；Green `f97a059` 在第一個精準錯誤後清除舊 room、停止排程並只導回首頁一次。Affected `15 passed`、Frontend `90 passed`；其他 `404` 與房主主動刪房行為未退化，代表性 sensitivity 可抓到 guard 失效。修正已隨 Batch 10A 部署，但測試房停在 `LOBBY`，正式 UI 只允許刪除 `COMPLETED` 房間，因此 AWS 多分頁刪房 gate 尚未執行。
- PR #4 已更新 metadata 並以 merge commit `d94e47b` 合併至 `main`；合併後 GitHub Actions run `32544076633` 的 Backend／Frontend jobs 均通過。合併沒有部署權限，AWS active release 未改變。
- 世界尚未開放的 join `409` 已完成 R1 TDD：Red 精確證明原始「只有等待中的房間可以加入玩家」不具體；Green `afe63bd` 將 `409 + ROOM_NOT_JOINABLE` 映射為「房主尚未開放世界，請稍後再試。」。Landing Page `8 passed`、Frontend `92 passed`；合併前 PR #5 GitHub Actions run `32553658881` 的 Backend／Frontend jobs 均通過。
- PR #5 已以 merge commit `de49944` 合併至 `main`；合併後 GitHub Actions run `32557825420` 的 Backend／Frontend jobs 均通過。Release `tier0-20260822-de49944` 已部署：`co-story.tar.gz` 約 `138 KiB`，SHA-256 `d686adecc932747141c9f0c1e3b8077cc705479b4bea6879155429a65a7cff8b`，S3 exact objects `2`、EC2 checksum `OK`；application／public edge／renewal timer active、staging inactive，readiness／public HTTPS `200`，previous release `tier0-20260822-8bb6bfc`。
- 甘特圖 M4 原訂 8/25 完成 Tier 1–2，目前已落後；後續依縮減原則先交付每層一個可驗證案例，不以擴張 AWS 常駐資源追回時程。
- 世界生成前回合上限回復預設 `6` 已完成 R2 TDD：Red `28f0127` 重現房主選 `8` 後生成草稿變回 `6`；Green `8a27aa4` 只保留尚未確認的表單選項，不提前寫入 canonical state，已隨 Batch 10A 部署。Batch 10A 另發現 confirm `422` 後回合上限從 `8` 回到 `6`；後續 Green `9ff0506` 只在確認失敗時恢復送出前選項，Targeted `1 passed`、Affected `4 passed`、Frontend `92 passed`，尚未部署。
- 節費操作由使用者透過 AWS Console 進行；2026-08-22 private PostgreSQL RDS 曾停止後為 Batch 10A 啟動，目前維持運行。因近期仍會頻繁使用，專題採「預估超過 48 小時不使用才停止」的操作門檻；這不是 AWS 規則。停止期間不計 DB instance hours，但 storage／backup 仍計費，且最長 7 天會自動啟動。
- Batch 10A 已部署 `tier0-20260822-8bb6bfc`：exact S3 objects `2`、checksum `OK`；application／public edge／renewal timer active、staging inactive、readiness／HTTPS `200`、首頁 `no-store`，previous release 保留 `tier0-20260819-ee128da`。世界未開放提示、角色儲存與 iPhone Safari 雙向同步均通過；Desktop → Safari 延遲小於 10 秒，雙方 refresh 後 RDS persistence 正常；未呼叫 Bedrock。完整證據見 `docs/evidence/2026-08-22-tier0-stabilization-release/validation.md`。
- Tier 1 repo-local gap analysis 已完成；第一個 R3 TDD slice 亦已完成：Red `8f5aea8`／`3e33e5f`、Green `66cf913`。設定 `CO_STORY_APPLICATION_LOG_PATH` 後，只接受 request／Storyteller 精確 allowlist schema，排除 query、raw access line 與 forged extra field；檔案為 `0640`、1 MiB rotation、最多兩份 backup 並拒絕 symlink target。Targeted `4 passed`、Backend `315 passed, 8 skipped`，三類 safety sensitivity 皆有效；驗證見 `docs/evidence/2026-08-22-tier1-safe-log-file/validation.md`。程式已包含於 active release，但 runtime environment 是否啟用該 sink 尚未實機確認。
- Tier 1 CloudWatch Agent repo-local contract 已完成：Red `0c166c8`／`7f5da34`、Green `b347abe`。Agent config 只讀 `/var/log/co-story/application.jsonl` 並指向固定 `/co-story/tier1/application`／`{instance_id}`；排除 system／auth／Nginx／wildcard source 與 metrics，candidate 使用獨立未收集的 JSONL。Affected `31 passed`、Backend `317 passed, 8 skipped`，三類 sensitivity 皆有效；驗證見 `docs/evidence/2026-08-22-tier1-cloudwatch-agent-contract/validation.md`。Batch 11A 已建立目標 Log Group／IAM；Batch 11B 已成功安裝 Agent package，但尚未啟用或驗證 log delivery。
- Tier 1 Log Group／IAM repo-local IaC 已完成：Red `9c50ec4`／`ad4bc05`、Green `2250bd3`。Template 只建立固定 Standard Log Group（7 天 retention、stack cleanup 刪除）與單一 managed policy；寫入權限限定 `${AppInstanceId}` stream，禁止 group management、wildcard resource 與其他 principal。Affected `20 passed`、Backend `323 passed, 8 skipped`，五類 sensitivity 全數有效；R3 Sol review 無 High／Critical blocker。驗證見 `docs/evidence/2026-08-22-tier1-observability-iac/validation.md`。已隨 Batch 11A deploy；policy 只附加 AppRole，Access Analyzer basic validation 四類 finding 皆 `0`，實際寫入正負測試待完成。
- Tier 1 5xx metric／alarm repo-local IaC 已完成：Red `cc208d4`／`aad2626`、Green `fc96f12`。Filter 精確限定 500–599；只建立無 dimensions 的單一 custom metric，Alarm 為 Sum／60 秒／1 of 1／threshold 1／missing notBreaching，明確停用所有 action。Affected `14 passed`、Backend `325 passed, 8 skipped`，六類 sensitivity 全數有效；R3 Sol review 無 High／Critical blocker。驗證見 `docs/evidence/2026-08-22-tier1-application-5xx-alarm/validation.md`。已隨 Batch 11A deploy，Alarm 初始為 `OK`；尚未產生 trigger／recover evidence。
- Tier 1 受限 SSM health-check 的 versioned route 修正已依 R3 TDD 完成：Red `dcd8efd`、Green `529d223`，固定檢查 `/api/v1/live`、`/api/v1/ready`；targeted `5 passed`、Tier 1 affected `15 passed`、Backend `330 passed, 8 skipped`，舊 `/live` sensitivity 有效。AWS Document 仍是 Batch 11A 舊版本且從未執行；必須先透過 Change Set 更新 stack。
- Tier 1 Batch 11A 已由使用者透過 Tokyo Console 部署：`co-story-tier1-observability` 四項資源與 `co-story-tier1-operations` 的 `HealthCheckDocument` 均回報 `CREATE_COMPLETE`，Alarm 初始為 `OK`。兩份 Change Set 精確為四筆與一筆 `Add`，ID 已遮蔽；policy 只附加 `AWSFinalProjectAppRole`，Access Analyzer 顯示 `Security／Errors／Warnings／Suggestions = 0`；未安裝 CloudWatch Agent、未執行 SSM Document 或 Bedrock。驗證見 `docs/evidence/2026-08-23-tier1-foundation-deployment/validation.md`。
- Tier 1 Batch 11B 已部分執行：使用者透過 SSM Distributor 成功安裝 `amazon-cloudwatch-agent-1.300071.0b1720-1.aarch64`。首次 runtime 設定在 restart 後立即檢查 loopback 得到 `curl (7)` 並 rollback；後續單次唯讀 audit 已確認 application active、runtime log env absent、JSONL absent、Agent inactive，production 安全恢復。下次重試必須以固定期限輪詢 `/api/v1/ready`，成功後才啟動 Agent，逾時 rollback；不得直接重跑首次命令。驗證見 `docs/evidence/2026-08-24-tier1-runtime-observability/validation.md`。
- Batch 10B zero-model Browser gate 在匿名房 `LRTPGC` 重現：完整重載部署後前端，選 `8` 回合並送出會由 Backend 回 `422` 的短欄位；欄位錯誤正確顯示，但後續 DRAFT polling 又將選項覆寫為 canonical `6`。依停止條件未呼叫 Bedrock。根因為既有 `9ff0506` 只覆蓋 command error 後的同步 restore，沒有覆蓋下一次 polling render。
- DRAFT polling round-state 已完成後續 R2 TDD：Red `8dc7592` 精確得到 `'6' !== '8'`；Green `1940b8b` 只在 incoming room 仍為 DRAFT 時跨 polling render 保留未確認選項，離開 DRAFT 仍接受 canonical state。Targeted `1 passed`、affected `16 passed`、Frontend `93 passed`；PR #6 已以 merge commit `c5c1541` 合併，main CI 全綠，尚未部署。驗證見 `docs/evidence/2026-08-22-confirm-world-round-preservation/validation.md`。
- Polling 修正 release `tier0-20260822-c5c1541` 已由 exact main merge commit 建置；`co-story.tar.gz` 約 `138 KiB`，SHA-256 `ce035e329e37f38b742dee78f21217b72b4696603a2be1927e3d561ec19de122`。Batch 10C 以 S3 exact objects `2` 上傳、EC2 checksum `OK` 後部署；application／public edge／renewal timer active、staging inactive，readiness／public HTTPS `200`，previous release `tier0-20260822-de49944`。
- Batch 10C zero-model Browser gate 已通過：匿名房 `LRTPGC` 選 `8` 回合並取得 Backend `422` field errors，返回當下與等待 `4.2` 秒、跨至少一次 polling 後均維持 `8`。
- Batch 10C exactly one Bedrock 世界生成已成功：匿名 benign 關鍵字「雨夜／山村／風車」，生成剩餘次數 `2 → 1`，產生完整 canonical world draft；生成後再等待 `4.2` 秒仍維持 `8` 回合，未重試模型。當時發現先前 `422` field errors 在成功生成後仍殘留。
- Stale world field-error UX 已完成 R2 TDD：Red `3863404` 精確證明成功生成後 `aria-invalid` 仍為 `true`；Green `6e9de5a` 只在生成成功後清除舊 field errors，再回填 canonical draft。Targeted `1 passed`、affected `6 passed`、Frontend `94 passed`；PR #7 已以 merge commit `9dc2350` 合併，尚未部署。

## Next

```text
Batch 9B release 與零模型 Browser gate已完成
→ Batch 9C exactly 1 次 synthetic prompt-injection smoke 回 SCHEMA_INVALID／503，未通過
→ Batch 9D 已部署 application-layer 明確注入拒絕，零 Bedrock rejection gate 通過
→ 四玩家四回合外部試玩與 backend evidence 已完成
→ 第一次進度書面報告與 13 頁簡報已完成、通過 audit 並 push
→ 純 CI foundation 已完成本機 Red／Green、完整 regression 與 GitHub-hosted runner 驗證
→ 公開 JavaScript exception 已完成 R2 TDD並於 Batch 10A 部署，Desktop Browser gate 通過
→ 刪房後其他分頁的 `404` 導頁／polling lifecycle 已完成 R2 TDD 並部署；待下一個已完成房間做 AWS Browser gate
→ PR #4 已合併，合併後 main CI 全綠
→ Batch 10A stabilization release 與 Safari 雙向同步已通過；RDS 因近期頻繁使用暫時維持運行
→ Tier 1 安全 JSONL、Agent collection、Log Group／最小 IAM、5xx metric／alarm contract 已完成本機 R3 TDD；Batch 11A AWS foundation 已部署
→ 世界尚未開放的 join `409` 明確玩家提示與 confirm `422` form-state 修正已隨 PR #5 合併，main CI 全綠
→ `tier0-20260822-de49944` 已部署且 runtime gate 通過；zero-model 422 gate 發現 DRAFT polling reset，未呼叫 Bedrock
→ DRAFT polling round-state Red／Green 已隨 PR #6 合併，main CI 全綠；尚未部署
→ `tier0-20260822-c5c1541` 已部署；zero-model 422＋polling 與 exactly-one Bedrock generation＋polling gates 全數通過
→ 成功生成後清除舊 422 field errors 的 Red／Green 已隨 PR #7 合併，main CI 全綠；尚未部署
→ Tier 1 parameter-free SSM health-check Red／Green、完整 regression 與四類 R3 sensitivity 已完成
→ Batch 11A observability 四項資源與 operations SSM Document 已部署；Alarm `OK`
→ Batch 11B Agent package 安裝成功；runtime 設定因 restart 後 loopback `curl (7)` rollback，唯讀 audit 已確認 production 恢復且 Agent inactive
→ SSM health document versioned route 修正 Red／Green、affected suite、完整 Backend regression 與 sensitivity 已通過；待 Change Set 更新 AWS 舊版本
→ 製作去識別化報告截圖、完成延遲成本檢查
→ 第一次報告後依清理計畫停止或刪除持續計費資源，再進入 Tier 1
```

下一個執行起點：Batch 11B 已核准且尚未完成。rollback audit 與 health document repo-local 修正均已完成；先由使用者透過 Console 建立 operations stack Change Set，精確確認只更新 `HealthCheckDocument`，執行並確認新 Document version 後才能 Run Command。runtime 設定重試另使用 bounded readiness wait，再續行安全 JSONL／log delivery gate。仍禁止 Agent 執行 AWS CLI、S3 讀取或 Bedrock 呼叫。

## Residual risks

- Prompt Attack 代表性測試明確得到 `SCHEMA_INVALID`／`503`，而非 Guardrail intervention；現有 Guardrail 不可作為唯一防線。
- IAM Access Analyzer basic policy validation 已在 Console 顯示 `Security／Errors／Warnings／Suggestions = 0`；尚未執行 runtime log-write 正／負測試。
- Batch 11B rollback 已確認 application active、runtime env 設定與 JSONL absent、Agent inactive；首次 `curl (7)` 的唯一根因仍未證實，下次只能以 bounded readiness wait 重試並保留 rollback。
- `CoStoryHealthCheck` repo-local route 已修正，但 AWS 上仍是錯誤的舊版本且尚未執行；Change Set update 前不得用它作為 Tier 1 證據。
- Direct IP certificate 約 160 小時效期；必須保留 renewal timer 驗證。EC2 stop/start 若 public IP 改變，URL、certificate 與 allowlist 都需重建。
- Idempotency store 仍是 process memory，不宣稱 multi-process exactly-once。
- iPhone Safari 在 Batch 10A 的 Lobby 雙向同步小於 10 秒且 refresh 後正常；先前公開試玩的不穩定現象未取得可重現根因，仍需在下一次完整多人遊戲觀察長時間 polling／visibility 行為。
- 角色儲存安全化已部署並通過 Browser gate；confirm `422` 與 DRAFT polling 的 8 回合保留已在 `tier0-20260822-c5c1541` 通過 zero-model 及 exactly-one-call AWS Browser gates。
- 成功生成後清除先前 `422` field errors 的 Green `6e9de5a` 已隨 PR #7 合併，AWS active release 尚未包含此修正。
- 成功刪房後舊分頁 polling 修正已部署，但尚未以 `COMPLETED` 房間執行 AWS 多分頁重驗。
- EC2 與 RDS 最近一次已知狀態均為運行中。RDS 會持續產生 DB instance hours；若預估超過 48 小時不使用則手動停止。EC2 若 stop/start 會更換 public IP，使目前 IP certificate 與 allowlist 都需重建；artifact objects 依 7 日 lifecycle 到期，但 stack／bucket不會自動刪除。
- 原始截圖位於 macOS TemporaryItems／Downloads 時不算正式 evidence；入庫前須去除 account ID、ARN、IP、instance／subnet／SG ID、endpoint、secret ARN、bucket suffix、通知與不必要的 Browser 資訊。
