# 平行分支工作邊界

- 狀態：Active
- 生效分支：`codex/story-quality`、`codex/tier3-delivery`、`codex/tier3-production-release`、`codex/tier3-healthcheck-correction`、`codex/tier2-components`、`codex/support-agent-core`
- 機器可讀規則：`.agents/work-boundaries.json`
- 自動檢查：`scripts/check_branch_boundaries.py`

## 目的

多個 Codex task 使用獨立 Git worktree 平行工作，但共享同一個 Git repository 與最終 AWS environment。本規範以路徑白名單、protected paths 與單一整合責任人避免檔案覆寫、語意衝突和相互部署。

白名單之外一律拒絕。分支不得自行修改本文件、policy、checker 或 protected paths；需要擴張範圍時，停止工作並回到整合 task 修改治理基準，再讓兩個分支同步新 commit。

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
