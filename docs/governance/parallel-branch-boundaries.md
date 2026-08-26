# 平行分支工作邊界

- 狀態：Active
- 生效分支：`codex/story-quality`、`codex/tier3-delivery`
- 機器可讀規則：`.agents/work-boundaries.json`
- 自動檢查：`scripts/check_branch_boundaries.py`

## 目的

兩個 Codex task 使用獨立 Git worktree 平行工作，但共享同一個 Git repository 與最終 AWS environment。本規範以路徑白名單、protected paths 與單一整合責任人避免檔案覆寫、語意衝突和相互部署。

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

## 共用檔案與交接

`AGENTS.md`、policy、checker、治理文件、README、CURRENT、checkpoints、task list、deployment log、project plan 與 source-of-truth 都是 protected paths，只能由整合 task 修改。

若任一分支需要另一分支擁有的檔案：

1. 立即停止該項修改，不繞過 checker。
2. 回報所需路徑、理由、最小差異與阻塞影響。
3. 由整合 task 決定轉移 owner、建立 shared contract commit，或調整 policy。
4. 分支同步治理 commit 後再繼續。

不使用 force push、rebase 或把另一分支未審核的工作直接覆蓋進來。

## Git 與整合順序

兩個分支必須從同一個已 push 的治理基準建立獨立 worktree，且各自 commit／push。建議整合順序：

1. Tier 3 delivery foundation 通過 container 與 workflow contract。
2. Story quality 通過 Backend／Frontend regression 與 deterministic Storyteller tests。
3. 整合 task 合併兩條分支並執行完整 Backend、Frontend、container build 與 boundary checks。
4. 只有整合 tip 全綠，才建立 production deployment batch。

Git worktree 可隔離檔案系統，但不能消除所有語意衝突；最後仍必須由整合 task review 合併結果。

## AWS 單一寫入者

Tier 3 delivery task 是唯一可準備 AWS／deployment 變更的工作線；使用者是單一部署 owner。任何時間只允許一個 production deployment batch，且必須綁定 exact commit SHA、image tag、health gate、rollback 與 previous release。

Story quality task 只能產生 repo-local commits，不得改變 active release。整合 task 也不能在未取得使用者對 bounded batch 的明確核准前擴張 IAM、建立計費資源或部署 production。

## 必要檢查

分支在每次 commit 前以其共同基準執行：

```bash
python3 scripts/check_branch_boundaries.py \
  --branch "$(git branch --show-current)" \
  --base <共同治理基準> \
  --head HEAD
```

回傳 `branch_boundary=passed` 才可交付。Pull request 會再次執行相同 checker；registered branch 的越界檔案會以 exit code `2` 阻擋。
