# AGENTS.md

本文件提供給 Codex、Claude Code、Cursor 或其他 AI Agent 使用，說明本專案的背景、工作原則、必要技能與文件規範。

## 專案定位

本專案是 AWS 雲端工程師培訓期末專題，以同一個「共演計劃」多人 AI 故事應用為主題；本次交付完成可運作的 AWS 架構、可觀測性、組件化與自動部署，微服務化與完整 Agentic AI 保留為未來方向。

> 重要：Tier 0–5 是同一產品的課程能力對映，不是六選一。但依 [ADR-0008](docs/decisions/0008-fix-final-delivery-scope.md)，2026-09-07 最終交付範圍已收斂為 Tier 0–3 對應的 AWS production 可玩 MVP、可觀測／SSM、Web／Worker／Data 組件化與自動部署。Tier 4／5 只是 future roadmap，不得當成當前未完成項或自動啟動的 backlog。

主要路線：

```text
Final delivery：
Tier 0  共演計劃可玩 Web App + 公私網段 + 私有資料層
  -> Tier 1  CloudWatch 可觀測性 + AIOps + SSM 免 SSH
  -> Tier 2  Web／Story Worker／Data 組件切割與網段隔離
  -> Tier 3  Docker + ECR + GitHub Actions OIDC CI/CD

Future roadmap／out of scope：
Tier 4  Lobby／Character／Turn／Rules／Story 微服務
Tier 5  Prompt 管理 + RAG + MCP／工具 + 多 Agent + AI 監控
```

`WordPress Web/DB 分離` 是簡報中的 Tier 0 題目範例與架構基準，不是本專題既定產品。若講師要求逐字完成該題卡，再另建 ADR，不得自行把 WordPress 插入共演計劃核心。

## Agent 開工讀取策略

每個新 task 的最小啟動集只有：

1. `AGENTS.md`
2. `docs/product/source-of-truth.md`
3. `docs/handoffs/CURRENT.md`

其餘文件依任務路由按需讀取：

- 程式／API／UI：`docs/testing-strategy.md`、當前 Feature Spec、相關 ADR 與目標程式碼。
- 遊戲規則：只讀正式 MVP Spec 的相關章節。
- AWS／IAM／成本／部署：專題 Skill、Project Plan、Checkpoints、成本／安全證據與 Skill 指定 reference。純本機 MVP coding 不載入 AWS Skill。
- 時程／課程對照：Project Brief、Gantt、course requirements alignment。
- 原始 `docs/inbox/專題.pptx`：只在課程要求有歧義或需要核對原頁時讀取。
- 全域規劃／final review：才讀 README、Project Brief、project plan、gantt 與 checkpoints 全集。

禁止為建立背景而遞迴讀取整個 `docs/`。同一 task 內已完整讀取且未變更的文件不得重讀；先用 `rg` 定位檔案與章節，再讀必要範圍。測試輸出只保留 pass／fail 摘要與失敗片段。若任務涉及 AWS 實作，仍必須確認目前 AWS 成本、安全與資源狀態，不可假設環境已準備完成。

## 平行分支工作邊界

若目前 branch 存在於 [`.agents/work-boundaries.json`](.agents/work-boundaries.json)，開工前必須完整讀取該 policy 與 [`docs/governance/parallel-branch-boundaries.md`](docs/governance/parallel-branch-boundaries.md)。只能修改該 branch 的 `allowed_paths`；`protected_paths` 與白名單外路徑一律禁止。需要擴張權限時停止工作並交回整合 task，不得自行修改 policy、checker 或治理文件。交付前必須執行 `scripts/check_branch_boundaries.py` 並取得 `branch_boundary=passed`。

## 風險式模型路由

- R0（文件、格式、rename、inventory）：Luna；不可用時使用 Terra low。
- R1／R2（例行或跨層 coding、tests、docs、debugging）：Terra 主導並自行 QA。
- R3（Auth、session、migration、IAM、成本、不可逆操作）：Sol 只做一次前置決策或完成前安全 review，不逐 assertion 重審。
- 單一局部任務不為湊比例啟動 subagent。需要分工時使用短 task packet 與有限 turns；禁止多個 Agent 重讀同一批 evidence，回傳只保留結論、風險與必要檔案位置。

## 核可邊界與常設授權

已在 Approved Spec、Accepted ADR 或 approval log 核准的產品行為視為常設授權，不得換一份 Feature Spec 再要求使用者核准。Agent 可自主決定可逆的實作細節，例如 UTC、Clock injection、內部 API／class 拆分、測試 fixture、命名、refactor 與安全的錯誤預設，並以測試與 commit 留痕。

只有以下差異需要詢問使用者：新增／改變產品行為、上游規格衝突、成本上限或架構範圍明顯擴張、IAM 權限提升、Root／MFA／帳務、外部傳輸、刪除大量資料、production deploy 或其他不可逆操作。詢問時只列「差異、建議值、影響」，不要求 review 整份 Spec 或 evidence。

使用者已授權下列 repo-local 操作自動執行；執行環境若仍要求 sandbox approval，必須遵守工具核准，文件不得繞過：

| 類別 | 自動執行 | 需人工／條件式核准 |
| --- | --- | --- |
| Git 讀取／本機歷史 | `status`、`diff`、`log`、列出 branch、`add`、`commit`、建立 local branch、local checkpoint commits | merge 到主要 branch、rebase、刪除 branch、`reset --hard`、`clean -fd`、force push |
| Repo 工作 | 建立／修改 repo 內檔案、formatter、lint、test、build；大量刪除若有精確 repo-local 清單、可復原且 auto-review 無異常，可自動執行 | 大量刪除的範圍不明、不可復原或超出 repo 時詢問 |
| 遠端 Git | `fetch` 可自動；工作樹乾淨且不需 rebase／衝突處理時可 `pull --ff-only` | `push` 只有使用者在當前任務明確要求時自動，否則詢問 |
| 憑證／雲端 | 無 | 任何 AWS CLI batch、修改 `~/.ssh`、`~/.aws`、Keychain、GitHub release、production deploy；憑證位置預設禁止修改，除非使用者明確指定 |

## 文件語言規範

給使用者、講師、同學、面試官閱讀的文件，一律使用繁體中文撰寫。

範例：

- README
- 專題規劃
- 甘特圖
- 檢核清單
- 架構說明
- Demo 說明
- 截圖註解
- 部署紀錄

以下內容可保留英文：

- AWS 服務名稱，例如 `VPC`、`EC2`、`RDS`、`CloudWatch`、`SSM`
- 程式碼、設定檔、CLI 指令
- GitHub Actions workflow
- Terraform/CDK/CloudFormation resource name
- API、package、module、function 名稱

## 專案中的 Agent 需要具備的技能

### 1. 專案治理與文件整理

Agent 需要能整理：

- 專題目標
- 交付格式
- 甘特圖
- 檢核點
- Demo 流程
- README 與部署紀錄

輸出應能直接給講師閱讀與驗收。

### 2. AWS 基礎架構設計

Agent 需要理解並能協助規劃：

- VPC
- CIDR
- Public subnet
- Private subnet
- Route table
- Internet Gateway
- NAT Gateway
- EC2
- RDS
- Security Group
- IAM role

核心原則：

- Web 可以對外。
- Database 必須放在 private subnet。
- DB 不可被 public internet 直接存取。
- Security Group 只開必要流量。

### 3. AWS 成本與安全

Agent 必須優先提醒並協助：

- 建立 AWS Budgets 告警
- 使用 Free Tier 或最小合理規格
- 避免不必要的高費用服務
- Demo 後清理或 terminate 資源
- 不把 secrets commit 到 GitHub
- 使用最小權限 IAM

如果任務可能產生 AWS 費用，Agent 必須先明確提醒使用者。

### 4. 可觀測性與維運

Agent 需要能規劃與實作：

- CloudWatch Agent
- CloudWatch Logs
- CloudWatch Metrics
- CloudWatch Dashboard
- CloudWatch Alarm
- 基本 incident simulation
- 維運 runbook

原則是先有 logs、metrics、dashboard，再導入 AI 分析。

### 5. SSM 免 SSH 維運

Agent 需要能協助：

- 設定 EC2 IAM role
- 啟用 Session Manager
- 使用 Run Command
- 規劃不開 public SSH 的維運方式
- 將修復流程寫成可展示的 Demo

講師已強調：不要依賴 SSH。

### 6. AI / AIOps

Agent 需要能設計：

- LangChain 維運 Agent
- CloudWatch log 分析流程
- 異常摘要
- Root cause analysis
- Recovery action 建議
- Agent 部署到 EC2 或 Lambda

Agent 必須避免做只有本機能跑的 Demo。AI 元件最終也要部署到 AWS。

### 7. DevOps 與 CI/CD

Agent 需要能協助：

- GitHub Actions
- Dockerfile
- ECR
- EC2 或 ECS deployment
- 基本測試與自動部署流程

加分目標是做到「改一行 code，可以自動 build 並部署到 AWS」。

### 8. 架構圖與視覺化

Agent 需要能產出：

- Mermaid 架構圖
- Network topology
- Demo 流程圖
- AI workflow
- Automation flow

圖表應能放入 README 或 `docs/`，並搭配 AWS 截圖作為證據。

### 9. GitHub 協作

Agent 需要能協助：

- 維護 README
- 建立 issue / milestone
- 撰寫 commit message
- 檢查 git status
- 避免 commit secrets、暫存檔與 `.DS_Store`

### 10. 風險式嚴格 Test-Driven Development

凡涉及 production code、API、遊戲規則、資料存取、IaC、workflow 或可觀察 UI 行為的變更，必須遵循 [`docs/testing-strategy.md`](docs/testing-strategy.md) 的嚴格 TDD 流程：

```text
Red：先寫測試並確認因缺少目標行為而失敗
  → Green：只寫讓該測試通過的最小實作
  → Refactor：不改行為地整理設計，重新通過全部測試
```

強制規則：

- Production 行為仍必須 test-first；Red 必須因缺少目標行為而失敗，不得以事後補測試冒充 TDD。
- 一個 cohesive feature／安全 invariant 可包含數個相關案例，不為每個 assertion 建立獨立治理循環。
- Red 只跑 targeted test；Green 跑 targeted＋受影響 suite；相關的完整 Backend／Frontend／contract regression 在 cohesive feature 完成或 merge gate 跑一次。
- R3 必須有負面／boundary／rollback 驗證，並對每類新 guard 做一個代表性 sensitivity；R1 不建人工 evidence，R2 只留短 validation manifest。
- 無實質 refactor 不需另建 commit、重跑完整 suite或撰寫「無需重構」段落。
- 功能分支最新狀態與 `main` tip 必須全綠；純文件、註解與格式化不強制 TDD。

## 工作原則

1. 先完成 Tier 0，再做延伸。
2. 優先建立可運作、可展示、可截圖的成果。
3. 文件採 milestone 更新：CURRENT 只記當前狀態，checkpoints 只在 Tier gate 改變，deployment log 只記實際 AWS／環境部署。
4. 開發中的詳細歷史留在 Git；不把同一狀態重寫到 README、daily、task list、evidence 與 handoff。
5. 任何 AWS 實作都要先考慮成本與安全。
6. 不要把本機 Demo 當成最終成果，成績以 AWS 實際運作為準。
7. 不要硬編 secrets。
8. 能用 SSM 時，不以 SSH 作為主要維運方式。
9. 所有程式行為變更採風險式嚴格 TDD；證據深度依 R0–R3 分級。

## 建議下一步

1. 以已完成的 AWS production 組件化與自動部署證據建立 5–8 分鐘 final Demo。
2. 整合 current architecture、證據索引、README 與課程能力對映。
3. 完成 repository secrets 與 tracked screenshots 去識別化稽核。
4. 完成 2026-09-08 資源清理 runbook 與帳單複查步驟；未核准前不執行 AWS 清理。
5. 不自動開始 Tier 4、完整 Tier 5 或 Support Agent Bedrock／RAG／external submit；這些都屬於新範圍。

## 完成定義

本次最終交付完成時，必須同時具備：

- AWS 上可驗證的實作
- GitHub 中可閱讀的文件
- 對應截圖或 Demo 證據
- 已依 ADR-0008 整合的驗收參考與證據索引
- 可向講師說明的架構理由
