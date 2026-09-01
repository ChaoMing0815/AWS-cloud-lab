# 平行分支工作邊界

- 狀態：Active
- 生效分支以 `.agents/work-boundaries.json` 為準；本輪新增 `codex/ui-terminal-refresh` 與 `codex/support-pixel-widget`。
- 機器可讀規則：`.agents/work-boundaries.json`
- 自動檢查：`scripts/check_branch_boundaries.py`

## 目的

多個 Codex task 使用獨立 Git worktree 平行工作，但共享同一個 Git repository 與最終 AWS environment。本規範以路徑白名單、protected paths 與單一整合責任人避免檔案覆寫、語意衝突和相互部署。

白名單之外一律拒絕。分支不得自行修改本文件、policy、checker 或 protected paths；需要擴張範圍時，停止工作並回到整合 task 修改治理基準，再讓兩個分支同步新 commit。

## `codex/ui-terminal-refresh`

兩日切片只負責非 Support 的 Web 視覺改版：首頁顯示可人工遞增的 release／UI 版本標記，讓 digest release 後可從畫面辨識新版本；以新的同源 SVG 品牌圖示取代旋轉「共」菱形；保留夜色劇場色彩語意，加入系統等寬字體、終端狀態層級與必要的 responsive／reduced-motion 修正。Claude handoff 是設計建議，實際行為仍以正式 Spec、CURRENT 與 tests 為準。

強制邊界：

- `web/index.html`、`web/styles.css`、`game-page.js` 與列出的 UI tests 由本分支獨占；不得修改 `bootstrap.js`、Support 頁、Support Widget stylesheet 或 Support assets。
- 版本標記必須是玩家可見文字且包含穩定 DOM hook；本輪不改 Docker、workflow 或 release driver。每次要展示不同 CI/CD release 時，由整合 task 在候選 commit 明確遞增版本，不把靜態字串宣稱為自動產生的 Git SHA。
- AI `RESOLVING` 只改善既有狀態呈現；不得偽造串流、完成內容、自動 retry／cancel／fallback。逐字動畫只有在 Red／Green 測試、`prefers-reduced-motion` 與完整內容可立即進入 accessibility tree 均可證明時才納入，否則兩日版降級為靜態終端狀態。
- 新品牌圖示使用同源 SVG 或原生 CSS，不依賴外部字型、CDN、inline script 或第三方 asset。
- 分支只做 repo-local strict TDD、完整 Frontend regression 與 boundary check；不得自行 push、merge、觸發 workflow 或 production deploy。

## `codex/support-pixel-widget`

兩日切片把已部署的 bounded Support Agent 包裝成全站可開關的像素角色聊天視窗，使玩家保留當前頁面與遊戲狀態即可查規則或建立待確認草稿。既有 `/support` 頁可保留作為可分享／無 JavaScript fallback 的完整入口；浮動介面不得把固定的兩條 intent 偽裝成自由對話模型。

強制邊界：

- 本分支獨占 `bootstrap.js`、Support UI、`support-widget.css`、Support assets 與專屬 tests；不得修改 `index.html`、全站 `styles.css`、遊戲頁、Backend/API 或 release 檔案。
- Widget 以 JavaScript 建立 DOM 並載入同源 stylesheet；像素角色使用同源 SVG／PNG 或純 CSS，不新增外部 request、框架、字型或第三方依賴。
- 介面必須提供可見開關、Esc 關閉、focus return、合理 focus order、`aria-expanded`／dialog 語意、reduced-motion 與手機不遮擋核心操作的驗證。
- Anonymous 只能使用 cited／unsupported 規則查詢；有效 Player session 才能建立 `local_draft_only` 草稿。任何畫面都要保留「需人工確認、不會對外提交」，不得新增 Bedrock、RAG、MCP、external submit、任意 route switching 或新的 Backend capability。
- 分支只做 repo-local strict TDD、完整 Frontend regression 與 boundary check；不得自行 push、merge、觸發 workflow 或 production deploy。

## 本輪 UI 整合與部署順序

1. 兩分支從同一治理 commit 建立 worktree 並平行完成 Red → Green → Frontend regression → boundary check。
2. 整合 task 先 cherry-pick `codex/ui-terminal-refresh`，再 cherry-pick `codex/support-pixel-widget`；兩者沒有共同 owner 檔案，整合後仍須跑完整 Frontend 與 release contract regression。
3. 整合 task 在候選 release commit 核對首頁版本字串、CSP／無外部 request、桌機與手機互動、Support 安全語意及 secrets／screenshot audit。
4. Production 只走既有 GitHub OIDC／ECR／Trivy／SSM `digest-release`。觸發 workflow 與 production approval 是新的 bounded deployment batch，必須由使用者明確核准；兩個功能分支不得各自部署。

## `codex/story-quality`

唯一目標是改善實際遊玩價值：讓玩家行為、角色資訊、骰點、進度、危機與既有場景形成有因果關係的敘事，並改善直接相關的前後端體驗。

允許範圍以 policy 為準，主要包括：

- `backend/app/adapters/bedrock_storyteller.py`
- `backend/app/adapters/mock_storyteller.py`
- Storyteller、ending、world generation 直接相關 Backend tests
- `web/**`
- `docs/features/story-quality.md`
- `docs/architecture/llm-integration.md`
- 專屬 story-quality validation evidence

禁止事項：

- 不修改 Docker、GitHub Actions、IaC、`ops/` 或 AWS runbook。
- 不進行 AWS deploy，不呼叫 AWS CLI、S3 或 Bedrock。
- 不更新 CURRENT、checkpoints、task list、deployment log 或 README。
- 若需要新 dependency，只提出精確需求；dependency manifest 的 owner 由整合 task 指定。

## `codex/tier3-delivery`

唯一目標是完成 current monolith 的 Tier 3 delivery foundation：container contract、ECR、GitHub OIDC、CI/CD、SSM release、health gate 與 rollback。

允許範圍以 policy 為準，主要包括：

- Dockerfile、`.dockerignore` 與本機 container contract
- `.github/workflows/**`
- `infra/cloudformation/tier3-*.yaml`
- `ops/container/**`、release scripts 與 container-specific systemd unit
- Tier 3 architecture、runbook、tests 與 validation evidence

禁止事項：

- 不修改產品 domain、Storyteller、Prompt、Web UI 或遊戲規則。
- 不更新 CURRENT、checkpoints、task list、deployment log 或 README。
- Agent 不執行 AWS CLI、S3 讀取或 Bedrock 呼叫。
- Production AWS change 必須另有 bounded change envelope；使用者以 Console／SSM 操作。

## `codex/tier3-production-release`

唯一目標是完成 T3B production release 的安全前置與執行 handoff：處理已知 GitHub Actions runtime annotation、核對 workflow／runbook／release contract，準備 bounded change envelope，並在使用者另行核准後協助保存去識別化部署與 rollback 證據。

允許範圍以 policy 為準，主要包括：

- Tier 3 CI／release workflow 與對應 contract tests
- 既有 Tier 3 SSM release Document template（只限首次 container bootstrap／legacy rollback contract）
- `Dockerfile` 與 container contract（僅在 release gate 證明需要時）
- `ops/release/` 的 container deploy／metrics scripts 與 container systemd unit
- Tier 3 release runbook 與專屬 production-release evidence

禁止事項：

- 不修改產品 domain、Storyteller、Web UI、Tier 2 queue／job 或遊戲規則。
- 未取得新的 T3B change envelope 明確核准前，只能做 repo-local 準備，不得觸發 `workflow_dispatch`、push image、執行 SSM 或部署 production。
- Agent 不執行 AWS CLI、S3 讀取或 Bedrock 呼叫；Console／SSM 由使用者操作。
- 不更新 CURRENT、checkpoints、task list、deployment log、README、policy 或治理文件。

## `codex/tier3-healthcheck-correction`

唯一目標是修正首次容器切換後已確認的 Docker HEALTHCHECK Host header 不相容：production runtime 必須以既有 allowlist 中的 Host 探測固定 live／ready endpoint，且不得輸出 allowlist 或其他 runtime configuration。

允許範圍以 policy 為準，限於：

- `Dockerfile` 與 `ops/container/healthcheck.py`
- container contract tests
- 同一 Tier 3 production release validation evidence

禁止事項：

- 不修改應用程式 TrustedHost policy、IAM、OIDC、CloudFormation、SSM Document、release／rollback driver、Tier 2 或產品行為。
- 不更新 CURRENT、checkpoints、task list、deployment log、README、policy或治理文件。
- 分支只做 repo-local strict TDD 與 CI；不得觸發 workflow、push image、執行 SSM、AWS CLI、S3 或 Bedrock。
- 修正合併後只能以新 exact `main` SHA、現有 active digest 與 `digest-release` 形成新的人工核准 envelope；禁止重跑既有 workflow run。

## `codex/tier2-components`

第一階段唯一目標是建立 Web／Story Worker／Data 的本地組件依賴圖，以及 queue／job／idempotency 的純本機 contract。這個切片先新增 domain、port、memory adapter 與 tests，不接入現行 `RoomService`、API 或 production composition，因此不改變已部署行為。

第二階段允許在相同邊界內新增PostgreSQL story-job queue adapter與`002_create_story_jobs.sql` migration，將既有lease／fencing／retry contract落到可重啟的資料層；仍不得接入現行request flow、production composition或AWS。

第三階段允許建立尚未接入route與production composition的replay-safe story resolution application slice：以同一PostgreSQL transaction完成Room CAS與job建立，並以result inbox／completion outbox協調Data commit與queue completion。此階段只能從`RoomService`抽出並共用既有回合結果規則，不得把現行同步route改成非同步，也不得改變玩家可見行為。

允許範圍以 policy 為準，主要包括：

- `story_jobs` domain／application contract
- `StoryJobQueue` port 與 memory adapter
- story-job 專屬 tests
- PostgreSQL story-job adapter、專屬migration與integration tests
- Story resolution domain／application contract、memory transaction double、PostgreSQL coordinator、append-only `003` migration與專屬tests
- `RoomService`只允許抽取既有round-result純規則供同步與未接線application slice共用；現行public method、retry與route行為必須由characterization tests保持不變
- 既有migration readiness test；只允許把current-schema fixture更新為包含`002_create_story_jobs`，不得改production readiness行為
- 第三階段可把同一current-schema fixture精確更新為`001_create_rooms`、`002_create_story_jobs`與`003_create_story_resolution_results`；empty、unknown與production readiness semantics不得改變
- Tier 2 component architecture、feature spec 與專屬 validation evidence

禁止事項：

- 除上述受限的`RoomService`純規則抽取外，不修改 API routes、schemas、`main.py` composition、Storyteller adapters、Web UI、database repository、Docker、workflow、IaC 或 `ops/`。
- 不執行 AWS deploy、AWS CLI、SSM、S3 或 Bedrock。
- 不更新 CURRENT、checkpoints、task list、deployment log、README、policy 或治理文件。
- Result transaction必須在queue completion前提交；Data rollback不得ack。Data commit後的completion failure必須可由inbox／outbox replay恢復，不得宣稱跨系統exactly-once。
- Story resolution local contract完成後必須交回整合task；需要接入現行request flow、SQS或production時，再由整合task審查並明確擴張allowed paths。

## `codex/tier2-async-flow`

唯一目標是把已合併的replay-safe Story Result接到玩家可見的非同步回合結算：API只建立job並回`202 Accepted`，獨立本機Worker處理敘事，Web透過既有房間讀取路徑觀察完成或失敗。此分支只驗證本機PostgreSQL與process邊界，不部署AWS。

允許範圍以policy為準，主要包括：

- resolve route／schema／serialization與production composition的必要接線
- Story resolution producer、Worker、PostgreSQL queue／store與專屬本機worker entrypoint
- Web API adapter、use case、presenter與玩家可見polling／timeout狀態
- API、composition、process restart、Web與既有Story Result contract tests
- Tier 2 async feature／architecture與短validation evidence

強制邊界：

- resolve POST只接受host授權、CSRF、room version與idempotency guard；成功回`202`、`RESOLVING`與opaque job ID，不在request內呼叫Storyteller。
- Web polling只讀既有room endpoint；逾時不得取消或重送job，也不得自動啟用fallback。Worker終局失敗寫`RESOLUTION_FAILED`後，才顯示既有人工retry／fallback控制。
- 同一idempotency key重送必須指向同一job；Room CAS與job建立保持單一PostgreSQL transaction。Data commit前不ack，completion replay invariant不得降級。
- 本機process E2E必須證明Web process與Worker process可分離，並覆蓋restart／duplicate delivery；未提供專用PostgreSQL測試DSN時明確skip，不得以memory double冒充restart證據。
- 不修改Docker、GitHub Actions、IaC、`ops/`、IAM、SQS或AWS資源；不執行AWS CLI／SSM／S3／Bedrock，不觸發production deploy。
- 不更新CURRENT、checkpoints、task list、deployment log、README、policy或治理文件；完成後交回整合task。

## `codex/support-agent-core`

唯一目標是建立尚未接入產品的bounded Support Agent核心：以靜態、版本化規則知識庫回答遊戲規則問題，並將問題整理成需要人工確認的本機report草稿。此分支不提供public API或UI，也不寫入PostgreSQL、GitHub、Email或其他外部系統。

允許範圍以policy為準，主要包括：

- Support Agent domain、application use case與專屬ports
- 靜態規則知識庫、Mock support model與memory report repository
- 不含secret的版本化`game_rules.json`
- 專屬tests、Feature／Architecture與validation evidence

強制邊界：

- 規則回答只能根據allowlisted rule records，必須附rule ID／title；無根據時明確回覆未定義，不得創造或修改canonical game rules。
- 問題回報第一階段只能建立草稿，必須經人工確認後才能在未來接正式submit tool；不得自動建立GitHub Issue、寄信或外部傳輸。
- 輸入與report必須拒絕或移除cookie、session／CSRF token、password、credential、runtime secret及其他敏感資料；測試不得使用真實secret。
- Tool selection固定allowlist；未知tool、額外參數、prompt injection與企圖改寫規則必須fail closed。
- 不修改共用`ports.py`、`RoomService`、API routes／schemas、`main.py`、Web UI、migration、Storyteller adapters、dependency manifest、Docker、workflow、IaC或`ops/`。
- 不呼叫Bedrock，不執行AWS CLI／SSM／S3，不接production；第一階段以Mock model與deterministic tests完成。
- 完成後交回整合task。必須等Tier 2本地PR合併後，才可重新評估migration編號、API／UI、Bedrock adapter、observability與自動部署，且需要新的allowed paths與production核准。

## `codex/tier2-production-worker`

唯一目標是讓PR #24建立的獨立Story Worker在production組態使用既有Bedrock能力，同時保持Web process不啟動Worker、local/test固定Mock，以及每次delivery最多一次模型呼叫且沒有application或SDK隱式retry。本分支只做repo-local strict TDD，不呼叫真實Bedrock、不部署AWS。

允許範圍以policy為準，主要包括：

- strict production storyteller factory、Worker entrypoint與snapshot narrator
- 既有Bedrock storyteller的單次複合round／ending輸出contract
- production composition、Worker isolation與單次invocation專屬tests
- Tier 2 async Feature／Architecture與短validation evidence

強制邊界：

- production缺少database、Region、model、guardrail或token設定時，必須在claim、client建立與model invocation前fail closed，且不得輸出設定值。
- 非最終與最終delivery皆最多一次`converse`；最終回合的round與ending必須由同一次複合輸出完成。模型失敗只做一次queue failure transition，不在同一delivery重試。
- Web application composition不得建立Worker thread、subprocess或background state；local/test不得建立Bedrock client。
- 不修改API、RoomService、repository、migration、Web、Docker、workflow、IaC或`ops/`；不執行AWS CLI／SSM／S3／Bedrock，不觸發production deploy。
- 真實PostgreSQL process/restart gate只能使用獨立、可清除且非production的測試DSN；缺少DSN時明確skip，不得以Mock冒充durable證據。
- 完成後交回整合task；任何AWS Worker／SQS部署需新的change envelope與人工核准。

## `codex/tier2-aws-worker-foundation`

唯一目標是準備已核准的Tier 2 AWS基礎：兩台無public IP的private Story Worker、SQS Standard Queue與DLQ、單一NAT Gateway、private subnet／route、SG、獨立Worker role與最小權限。此分支只做repo-local strict TDD、CloudFormation、ADR、架構與runbook；不得建立或修改AWS資源。

允許範圍以policy為準，主要包括：

- 單一`infra/cloudformation/tier2-worker-foundation.yaml`及其專屬contract tests。
- SQS／DLQ與private Worker的ADR、架構、部署runbook及短validation evidence。
- 課程驗收所需的三compute拓樸：既有public Web EC2加兩台private Worker EC2；RDS仍是private Data authority。

強制邊界：

- Worker數量固定為2，無public IPv4、無inbound規則，透過同一NAT Gateway進行必要outbound；不得新增ALB、ECS、EKS、Lambda、第二個NAT Gateway或Multi-AZ RDS。
- Queue使用SSE-SQS，不建立customer KMS key；DLQ必須有bounded redrive，訊息只含opaque job identifier與schema version，不放玩家文字、runtime secret或DB credential。
- Worker使用獨立IAM role；Web只取得指定Queue的最小producer權限，Worker只取得指定Queue consumer、既有ECR pull、SSM、CloudWatch、指定secret與既有Bedrock資源所需權限。禁止萬用`iam:PassRole`、管理員、SSH與任意secret讀取。
- DB SG只新增來自Worker SG的TLS PostgreSQL `5432`；Worker SG不得開inbound，NAT不得改變DB private/public狀態。
- 本分支不得修改產品Python、API、Web、migration、Docker、GitHub Actions、既有Tier 3 release template／driver、CURRENT、deployment log、checkpoints或其他protected path。
- 不執行AWS CLI／SSM／S3／Bedrock、CloudFormation Change Set、`workflow_dispatch`或production deploy。完成並合併後仍須由整合task形成獨立change envelope，由使用者在Console檢查與核准。
- 任何SQS adapter、visibility heartbeat、Worker runtime接線或玩家可見`async`切換都屬後續獨立分支，不得提前實作。

## `codex/support-agent-persistence`

唯一目標是以append-only `004` migration與PostgreSQL repository持久化Phase A已清理的Support Agent問題草稿，保留stable idempotency、divergent replay conflict、人工確認與local-draft-only邊界。本分支不提供API、UI、模型或外部submit能力。

允許範圍以policy為準，主要包括：

- Support Agent草稿domain／application持久化不變量與memory parity
- `004_create_support_report_drafts.sql`與PostgreSQL repository
- migration、repository、restart與migration readiness tests
- Support Agent persistence Feature／Architecture與短validation evidence

強制邊界：

- 只保存sanitized structured fields；不得保存raw description、raw identity、cookie、token、credential、runtime secret或外部submission state。
- `requires_human_confirmation`必須固定為true，submission狀態固定為`local_draft_only`；application、adapter與DB constraint均需fail closed。
- 本批不新增內容長度產品限制；長度與rate limit留到未來API切片決定。
- 不修改port、migration runner、`main.py`、routes、Web、Bedrock adapter、dependency、Docker、workflow、IaC或`ops/`；不執行AWS CLI／SSM／S3／Bedrock，不接production。
- 真實restart證據只能使用獨立、可清除且非production的專用PostgreSQL測試DSN；缺少時明確skip。
- `004`會改變全域migration readiness。分支可完成coding、push與PR，但在backward-compatible readiness／rollback策略另行完成前不得merge或部署；不得自行擴張至`postgres_room_repository.py`修正此問題。

## `codex/support-agent-durability`

唯一目標是以獨立、可清除且非production的PostgreSQL，驗證Support Agent草稿repository在真實並行競態下仍維持單一canonical row、stable idempotency與fail-closed conflict。本分支不接API、UI、模型、外部提交、AWS或production。

允許範圍以policy為準，主要包括：

- PostgreSQL Support draft repository的並行寫入contract與必要的最小修正
- 真實process／connection concurrency tests與短validation evidence
- Support persistence Feature中對已驗證並行語意的精確說明

強制邊界：

- 測試必須用同步barrier讓兩個獨立writer實際重疊；序列呼叫、單connection或Mock不得宣稱為parallel-write證據。
- 相同normalized draft與identity的兩個並行writer必須取得相同canonical draft，且資料庫只有一列。
- 共用idempotency key但payload不同時，只能保留一筆canonical row，另一方必須回`SupportReportConflict`；不得覆寫。
- 人工製造相同16位report ID prefix但payload不同時，只能保留一筆並回conflict；不得覆寫。
- 競態後仍須驗證row count、state、hash constraint與restart／replay語意。
- 只使用獨立、可清除且非production的專用PostgreSQL DSN；不得連production RDS，不得輸出credential或DSN。
- 若現有實作已通過並行contract，提交測試與證據即可；不得製造假Red或無必要修改production code。若精確測試揭露真實缺陷，才依strict TDD保留Red並做repository最小Green。
- 不修改domain、application、migration、migration runner、`main.py`、routes、Web、Bedrock adapter、dependency、Docker、workflow、IaC或`ops/`；不執行AWS CLI／SSM／S3／Bedrock，不接production。
- 可commit、push並建立PR；不得merge或deploy。完成後需主動回報整合task。

## `codex/tier2-migration-bridge`

唯一目標是在production套用`002`／`003`／`004`前，建立一個可驗證、可回復的過渡release。此bridge不套用新migration、不啟用async Worker，對外仍維持既有同步遊戲流程；待bridge成為verified active digest後，後續獨立batch才可套用append-only schema並啟用Tier 2 runtime。

允許範圍以policy為準，主要包括：

- migration inventory／readiness的明確向前相容contract
- production composition與route的bridge feature flag及fail-closed tests
- production Worker factory在bridge／sync mode下於queue、Bedrock client與claim前fail closed
- GitHub release input、release driver、stable unit與SSM Document的bounded bridge mode
- ADR、Tier 2／Tier 3架構、release runbook與短validation evidence

強制邊界：

- bridge mode不得執行migration，也不得建立、claim或處理StoryJob；玩家行為維持目前同步request flow。
- bridge readiness只能額外接受經audit的append-only版本`002`、`003`、`004`；任意未知、缺漏既有必要版本或重複／畸形migration state一律fail closed。
- bridge release與後續Tier 2 activation必須是兩個分離的change envelope；PR #25在bridge設計、回歸與rollback證據完成前維持`DO NOT MERGE`。
- release在任何guard失敗時不得切換target；rollback必須證明bridge可在newer schema下恢復既有同步服務，不得做schema downgrade。
- 本分支只做repo-local strict TDD、ADR與runbook；不執行AWS CLI／SSM／S3／Bedrock、`workflow_dispatch`或production deploy，也不修改IAM、OIDC、ECR、成本與migration SQL。
- 需要白名單外路徑時立即停止並交回整合task；完成後只可push／建立PR，不得自行merge。

## `codex/web-stale-feedback`

唯一目標是修正已完成 async 回合後仍殘留「AI 正在整理劇情」的玩家可見 feedback，並移除目前沒有 production API contract 的「建立新房間」圖示控制。此切片不得新增 room-code rotation、切換房間或 session 行為。

強制邊界：

- polling 讀到 canonical room 已離開 `RESOLVING` 時，必須清除只屬於該次 resolution 的 pending feedback；不得清除 API error、session expiry 或離線提示。
- `newRoomButton` 必須從正式與 Demo 共用 HTML 移除，且 `GamePage.mount` 不得再查找或註冊該節點；Mock 的結局重設測試仍維持原行為。
- 不修改 composition、API adapter、Backend、session、room code、CSS、MVP Spec、AWS 或 protected paths。
- 以 strict TDD 完成 targeted Red／Green與完整 Frontend regression；完成後只可 push／建立 PR，不得自行 merge 或 deploy。

## `codex/support-agent-api`

唯一目標是把既有 Support Agent 核心與已驗證 PostgreSQL draft repository 接入本機 HTTP API 與可 fail-closed 的 application composition。規則回答只能使用版本化 static rules；問題回報只建立需要人工確認的 `local_draft_only` 草稿。

強制邊界：

- 先在 `docs/features/support-agent-integration.md` 固定 request／response、錯誤、認證、CSRF、輸入上限與 rate-limit contract，Web 分支只讀取該 contract。
- 規則查詢可匿名；問題草稿必須由 server 端有效 Room／Player session 衍生 stable reporter identity，不接受 client 傳入 player ID、identity hash 或 submission state。
- 問題草稿 mutation 必須有 CSRF、bounded request size、idempotency 與 rate limit；錯誤不得回傳 cookie、token、DSN、raw exception 或敏感輸入。
- 不新增 migration，不改既有 room／story flow，不接 Bedrock、GitHub Issue、Email 或其他外部提交，不修改 Web、Docker、workflow、IaC、ops 或 protected paths。
- 本分支只做 repo-local strict TDD；不得執行 AWS CLI／SSM／S3／Bedrock或 production deploy。

## `codex/support-agent-web`

唯一目標是依整合 task 已固定的 Support Agent HTTP contract 建立規則問答與問題草稿 UI。UI 必須明確區分有引用的規則答案、查無根據，以及「尚未提交、需要人工確認」的本機草稿。

強制邊界：

- 只能呼叫固定 Support API；不得自行重作規則查詢、去敏、identity 或 report ID 演算法。
- 不提供或暗示 GitHub Issue／Email／外部送出；問題草稿不得顯示 cookie、token、identity hash 或 runtime metadata。
- Backend/API 分支先交付固定 contract；此分支可用 fake adapter strict TDD 平行開發，但 merge gate 必須在最新 Backend contract 上跑完整 Frontend regression。
- 不修改 Python、migration、Backend tests、AWS、Docker、workflow、IaC、ops、Feature Spec 或 protected paths。

## `codex/tier2-web-ui-release`

唯一目標是讓已合併的 stale feedback／失效房間控制 UI 修正透過既有 `digest-release` 上線時，精確保留目前 production Web 的 `async` resolution mode。此分支不開發 Support Agent，也不改 workflow、SSM Document、IAM、ECR、Worker、Publisher 或資料 schema。

強制邊界：

- strict TDD 必須先證明現有 release driver 會以 source unit 的 `sync` 覆蓋 active `async`，再做最小修正。
- `digest-release` 必須從 canonical installed unit 讀取並 allowlist `sync|async`；缺失、重複、空白、大小寫或未知值都在 registry login、pull、migration與 service mutation前停止。
- candidate、target unit promotion及 rollback 必須使用同一個已驗證 mode；不得只修最後一次 restart，也不得改寫 runtime／database env。
- `migration-bridge` 與 `schema-activation` 的既有 `sync` contract、digest fence、health、rollback及 fail-closed行為不得降級。
- 只修改 policy 白名單中的 release driver、contract tests、runbook與短 evidence；不得執行 AWS CLI／SSM／S3／Bedrock、`workflow_dispatch`或 production deploy。
- 完成後只可 push／建立 PR，不得自行 merge；production 必須由整合 task 以新的 exact main SHA、既有 active digest與人工 approval gate另行核准。

## `codex/support-csp-corrective`

唯一目標是消除 Support Agent production smoke 發現的 inline script 與 Google Fonts CSP 錯誤，同時保留 `file://` 的 server-required 提示。不得以放寬 CSP、加入 nonce／hash 或新增外部字型來源作為修正。

強制邊界：

- strict TDD 必須先證明 HTML 不含 inline script、CSS 不依賴外部字型，且既有 JavaScript module 負責 `file://` 提示。
- `default-src 'self'` 與現有 Backend CSP contract必須保持不變；不得加入 `unsafe-inline`、Google Fonts網域或其他第三方來源。
- 字型改用本機／系統 CJK font stack；不得新增字型 binary、package或網路請求。
- Support Agent API、草稿、遊戲流程、runtime config、release driver、AWS與protected paths均不得修改。
- 完成後只可push／建立PR；production必須由整合task在完整CI通過後，以新exact main SHA與當前active digest形成獨立`digest-release`人工核准 envelope。

### 下一輪整合順序

1. `codex/web-stale-feedback` 先合併，消除 `web/index.html` 的 owner 衝突。
2. 整合 task 固定 Support Agent HTTP contract 與共同治理基準。
3. `codex/support-agent-api` 與 `codex/support-agent-web` 從同一 exact base 平行開發；Backend 與 Web 路徑互斥。
4. 先合併 API，再讓 Web 分支同步最新 `main` 並完成 contract／Frontend merge gate。
5. `codex/tier2-web-ui-release` 與兩個 Support Agent 分支路徑互斥，可平行完成；它只服務已合併 UI patch 的獨立 production envelope。
6. Support Agent production deployment、Bedrock adapter與 external submit 均為後續獨立 change envelope。

## 共用檔案與交接

`AGENTS.md`、policy、checker、治理文件、README、CURRENT、checkpoints、task list、deployment log、project plan 與 source-of-truth 都是 protected paths，只能由整合 task 修改。

若任一分支需要另一分支擁有的檔案：

1. 立即停止該項修改，不繞過 checker。
2. 回報所需路徑、理由、最小差異與阻塞影響。
3. 由整合 task 決定轉移 owner、建立 shared contract commit，或調整 policy。
4. 分支同步治理 commit 後再繼續。

不使用 force push、rebase 或把另一分支未審核的工作直接覆蓋進來。

## Git 與整合順序

同時工作的分支必須從同一個已 push 的治理基準建立獨立 worktree，且各自 commit／push。目前下一輪建議整合順序：

1. `codex/tier3-production-release` 先完成 action runtime 相容性與 T3B repo-local preflight，停在人工核准前。
2. `codex/tier2-components` 完成不接入 production request flow 的第一個 story-job contract。
3. 整合 task 分別 review；production release 分支不得自動合併產品組件化變更後再部署。
4. T3B 只綁定已核准的 exact `main` commit；Tier 2 本地切片要進入下一次 release，必須另有整合與部署決策。

Git worktree 可隔離檔案系統，但不能消除所有語意衝突；最後仍必須由整合 task review 合併結果。

## AWS 單一寫入者

`codex/tier3-production-release` 是目前唯一可準備 AWS／deployment 變更的工作線；使用者是單一部署 owner。任何時間只允許一個 production deployment batch，且必須綁定 exact commit SHA、image tag、health gate、rollback 與 previous release。

Story quality 與 Tier 2 components task 只能產生 repo-local commits，不得改變 active release。整合 task 也不能在未取得使用者對 bounded batch 的明確核准前擴張 IAM、建立計費資源或部署 production。

## 必要檢查

分支在每次 commit 前以其共同基準執行：

```bash
python3 scripts/check_branch_boundaries.py \
  --branch "$(git branch --show-current)" \
  --base <共同治理基準> \
  --head HEAD
```

回傳 `branch_boundary=passed` 才可交付。Pull request 會再次執行相同 checker；registered branch 的越界檔案會以 exit code `2` 阻擋。
