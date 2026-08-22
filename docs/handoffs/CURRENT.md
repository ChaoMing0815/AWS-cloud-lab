# CURRENT：目前工作交接

- 更新日期：2026-08-22
- 近期目標：完成 Tier 0 公開試玩剩餘 bounded reproduction，同時暫停非必要 AWS compute 以節省 credits；之後依甘特圖縮減原則進入 Tier 1 最小可驗證切片。
- Branch：`codex/tier0-post-trial-stabilization`，由最新 `main` merge commit `d94e47b` 建立；回合上限保留 Green `8a27aa4`、Tier 1 安全 file sink Green `66cf913`、CloudWatch Agent contract Green `b347abe`，本文件狀態 commit 另計，尚未 push。
- 本機功能 checkpoint：公開試玩 UX／安全失敗記錄 `d2b76ba`；canonical route loading shell `f9d4155`；明確 Prompt Injection 前置拒絕 `6f872b2`；widow／orphan 排版規則 `18fcd21`；首頁公開試玩安全提示 `62b4e02`。
- Regression：Backend `317 passed, 8 skipped`；Frontend `91 passed`（2026-08-22，Tier 1 CloudWatch Agent contract Green gate）。
- AWS active release：`tier0-20260819-ee128da`。
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
- 尚未部署的本機 UI 收尾已依 TDD 完成：標題與段落使用 responsive `balance`／`pretty` wrapping，列印樣式避免單行跨頁；首頁移除硬編換行並加入「使用暱稱、勿輸入個資／機密」提示。Red commits 為 `a3337b0`、`bf8b193`；Green commits 為 `18fcd21`、`62b4e02`。
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
- 角色儲存原始 JavaScript exception 已完成 R2 TDD：Red `6d3c8fe` 精確證明未知 `TypeError.message` 會外露；Green `49aa5dc` 只允許 `ApiError`／`DomainError` 的 `publicMessage` 顯示，未知錯誤改為「角色儲存失敗，請重新整理後再試。」並保留輸入、canonical room、解除 busy。Targeted `3 passed`、Frontend `88 passed`，代表性 sensitivity 可抓回直接顯示原文的 mutation；GitHub Actions run `32496325155` 的 `backend-tests` 與 `frontend-tests` 均通過。驗證見 `docs/evidence/2026-08-21-character-error-safety/validation.md`；尚未部署。
- 刪房後舊分頁 polling lifecycle 已完成 R2 TDD：Red `a2b192d` 證明 `404 ROOM_NOT_FOUND` 仍會向外拋出；Green `f97a059` 在第一個精準錯誤後清除舊 room、停止排程並只導回首頁一次。Affected `15 passed`、Frontend `90 passed`；其他 `404` 與房主主動刪房行為未退化，代表性 sensitivity 可抓到 guard 失效。交付 tip `bfe3ce0` 已 push，GitHub Actions run `32542655388` 的 Backend／Frontend jobs 均通過；驗證見 `docs/evidence/2026-08-22-room-removal-polling/validation.md`。尚未部署或執行 Browser gate。
- PR #4 已更新 metadata 並以 merge commit `d94e47b` 合併至 `main`；合併後 GitHub Actions run `32544076633` 的 Backend／Frontend jobs 均通過。合併沒有部署權限，AWS active release 未改變。
- 甘特圖 M4 原訂 8/25 完成 Tier 1–2，目前已落後；後續依縮減原則先交付每層一個可驗證案例，不以擴張 AWS 常駐資源追回時程。
- 世界生成前回合上限回復預設 `6` 已完成 R2 TDD：Red `28f0127` 重現房主選 `8` 後生成草稿變回 `6`；Green `8a27aa4` 只保留尚未確認的表單選項，不提前寫入 canonical state。Affected `21 passed`、Frontend `91 passed`，代表性 sensitivity 可抓回退化；驗證見 `docs/evidence/2026-08-22-round-limit-preservation/validation.md`。尚未 push、部署或執行 Browser gate。
- 節費操作由使用者透過 AWS Console 進行；2026-08-22 private PostgreSQL RDS 已確認為 `Stopped`。DB instance hours 已暫停，storage／backup 仍計費，最晚約 2026-08-29 自動啟動；驗證見 `docs/evidence/2026-08-22-rds-temporary-stop/validation.md`。Agent 未執行 AWS CLI 或其他 AWS 寫入。
- Tier 1 repo-local gap analysis 已完成；第一個 R3 TDD slice 亦已完成：Red `8f5aea8`／`3e33e5f`、Green `66cf913`。設定 `CO_STORY_APPLICATION_LOG_PATH` 後，只接受 request／Storyteller 精確 allowlist schema，排除 query、raw access line 與 forged extra field；檔案為 `0640`、1 MiB rotation、最多兩份 backup 並拒絕 symlink target。Targeted `4 passed`、Backend `315 passed, 8 skipped`，三類 safety sensitivity 皆有效；驗證見 `docs/evidence/2026-08-22-tier1-safe-log-file/validation.md`。尚未部署，也未建立 CloudWatch／IAM／alarm／SSM AWS 資源。
- Tier 1 CloudWatch Agent repo-local contract 已完成：Red `0c166c8`／`7f5da34`、Green `b347abe`。Agent config 只讀 `/var/log/co-story/application.jsonl` 並指向固定 `/co-story/tier1/application`／`{instance_id}`；排除 system／auth／Nginx／wildcard source 與 metrics，candidate 使用獨立未收集的 JSONL。Affected `31 passed`、Backend `317 passed, 8 skipped`，三類 sensitivity 皆有效；驗證見 `docs/evidence/2026-08-22-tier1-cloudwatch-agent-contract/validation.md`。尚未安裝 Agent 或建立任何 AWS resource。

## Next

```text
Batch 9B release 與零模型 Browser gate已完成
→ Batch 9C exactly 1 次 synthetic prompt-injection smoke 回 SCHEMA_INVALID／503，未通過
→ Batch 9D 已部署 application-layer 明確注入拒絕，零 Bedrock rejection gate 通過
→ 四玩家四回合外部試玩與 backend evidence 已完成
→ 第一次進度書面報告與 13 頁簡報已完成、通過 audit 並 push
→ 純 CI foundation 已完成本機 Red／Green、完整 regression 與 GitHub-hosted runner 驗證
→ 公開 JavaScript exception 已完成 R2 TDD、push 與 GitHub CI；尚未部署
→ 刪房後其他分頁的 `404` 導頁／polling lifecycle 已完成 R2 TDD、push 與 GitHub CI；尚待 release Browser gate
→ PR #4 已合併，合併後 main CI 全綠
→ private PostgreSQL RDS 已停止；世界生成前回合選擇已完成本機 R2 TDD，再於短時 AWS window 重現 Safari sync
→ Tier 1 安全 application JSONL file sink 與 Agent collection contract 已完成本機 R3 TDD；AWS Log Group／IAM／alarm／SSM 尚未開始
→ 製作去識別化報告截圖、完成延遲成本檢查
→ 第一次報告後依清理計畫停止或刪除持續計費資源，再進入 Tier 1
```

下一個開發起點：依嚴格 TDD 建立 Tier 1 CloudFormation repo-local contract，預先定義固定 Log Group、7 天 retention 與只允許該 group／stream 的最小 logs write policy；先不 deploy。Agent 安裝、alarm、SSM document 與 incident AWS gate 必須逐段完成估價與另開 bounded batch。Safari sync 留到下一個經核准的短時 AWS release window。

## Residual risks

- Prompt Attack 代表性測試明確得到 `SCHEMA_INVALID`／`503`，而非 Guardrail intervention；現有 Guardrail 不可作為唯一防線。
- IAM Access Analyzer basic policy validation 未在 Console 顯示；CloudFormation、R3 tests、安全 review 與正負 Policy Simulator 已通過，但此項仍記為未執行。
- Direct IP certificate 約 160 小時效期；必須保留 renewal timer 驗證。EC2 stop/start 若 public IP 改變，URL、certificate 與 allowlist 都需重建。
- Idempotency store 仍是 process memory，不宣稱 multi-process exactly-once。
- iPhone Safari 未穩定取得即時 canonical state，需要手動重新整理；mobile sync 尚未達 Desktop Chrome 等價。
- 角色儲存原始 JavaScript exception 已在 `49aa5dc` 修正並通過 GitHub CI，但尚未部署；AWS active release 仍不得宣稱已具備此防線。
- 成功刪房後舊分頁持續 polling 已在 `f97a059` 修正並通過 GitHub CI，但尚未部署或以 AWS 多分頁重驗。
- EC2 最近一次已知狀態仍為運行中；RDS 已停止，storage／backup 仍計費且最晚約 2026-08-29 自動啟動。RDS 停止期間 public app readiness／遊戲操作不可用；EC2 若 stop/start 會更換 public IP，使目前 IP certificate 與 allowlist 失效。artifact objects 依 7 日 lifecycle 到期，但 stack／bucket不會自動刪除。
- 原始截圖位於 macOS TemporaryItems／Downloads 時不算正式 evidence；入庫前須去除 account ID、ARN、IP、instance／subnet／SG ID、endpoint、secret ARN、bucket suffix、通知與不必要的 Browser 資訊。
