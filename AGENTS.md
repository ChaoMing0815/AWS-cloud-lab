# AGENTS.md

本文件提供給 Codex、Claude Code、Cursor 或其他 AI Agent 使用，說明本專案的背景、工作原則、必要技能與文件規範。

## 專案定位

本專案是 AWS 雲端工程師培訓期末專題，目標是以同一個「共演計劃」多人 AI 故事應用為主題，先建立可運作的 AWS 傳統架構，再逐步演進成可觀測、可自動部署、微服務化與 Agentic AI 系統。

> 重要：Tier 0–5 是同一專題的累積演進階段，不是六選一，也不是做完 Tier 0 後任選一張題卡。每一層都要留下可運作成果、架構理由與驗證證據。

主要路線：

```text
Tier 0  共演計劃可玩 Web App + 公私網段 + 私有資料層
  -> Tier 1  CloudWatch 可觀測性 + AIOps + SSM 免 SSH
  -> Tier 2  Web／Story Worker／Data 組件切割與網段隔離
  -> Tier 3  Docker + ECR + GitHub Actions OIDC CI/CD
  -> Tier 4  Lobby／Character／Turn／Rules／Story 微服務
  -> Tier 5  Prompt 管理 + RAG + MCP／工具 + 多 Agent + AI 監控
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
- AWS 寫入：專題 Skill、Project Plan、Checkpoints、成本／安全證據與 Skill 指定 reference。
- 時程／課程對照：Project Brief、Gantt、course requirements alignment。
- 原始 `docs/inbox/專題.pptx`：只在課程要求有歧義或需要核對原頁時讀取。
- 全域規劃／final review：才讀 README、Project Brief、project plan、gantt 與 checkpoints 全集。

禁止為建立背景而遞迴讀取整個 `docs/`。同一 task 內已完整讀取且未變更的文件不得重讀；先用 `rg` 定位檔案與章節，再讀必要範圍。測試輸出只保留 pass／fail 摘要與失敗片段。若任務涉及 AWS 實作，仍必須確認目前 AWS 成本、安全與資源狀態，不可假設環境已準備完成。

## 模型路由

- 約 70% 使用 Terra：coding、tests、docs、一般 refactor、debugging、implementation。
- 約 20% 使用 Luna 處理 search、extract、rename、format、inventory、classification、cleanup；若 Luna 不可用，改用 Terra low reasoning。
- 約 10% 使用 Sol：architecture、SSOT、security、major bug、cross-layer conflict、final review。

比例是長期路由原則，不為湊比例切換模型；混合任務只把高價值決策交給 Sol。

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

### 10. 嚴格 Test-Driven Development

凡涉及 production code、API、遊戲規則、資料存取、IaC、workflow 或可觀察 UI 行為的變更，必須遵循 [`docs/testing-strategy.md`](docs/testing-strategy.md) 的嚴格 TDD 流程：

```text
Red：先寫測試並確認因缺少目標行為而失敗
  → Green：只寫讓該測試通過的最小實作
  → Refactor：不改行為地整理設計，重新通過全部測試
```

強制規則：

- 不得先寫 production implementation 再回頭補測試。
- 每個行為切片必須保存 Red、Green、Refactor 的指令、結果與 commit 對應。
- Red 必須是預期 assertion failure，不得是語法、import、環境或測試資料錯誤。
- Green 除目標測試外，必須通過既有 regression suite。
- 規則、安全、權限與 idempotency 變更必須做一次 mutation／故障注入敏感度驗證，證明測試會抓到刻意錯誤。
- 功能分支完成 Green 前不得合併；`main` tip 必須維持全綠。
- 若 Agent 發現 production code 已先被修改，必須停止該切片、回復尚未提交的 implementation，再從 Red 重新開始；不得以事後補測試冒充 TDD。
- 文件、註解、純格式化與不改變行為的素材調整不強制 TDD；但不得藉此規避實際行為測試。

## 工作原則

1. 先完成 Tier 0，再做延伸。
2. 優先建立可運作、可展示、可截圖的成果。
3. 每次實作都要同步更新文件。
4. 每個階段都要對應 `docs/checkpoints.md`。
5. 任何 AWS 實作都要先考慮成本與安全。
6. 不要把本機 Demo 當成最終成果，成績以 AWS 實際運作為準。
7. 不要硬編 secrets。
8. 能用 SSM 時，不以 SSH 作為主要維運方式。
9. 所有程式行為變更採嚴格 Red／Green／Refactor TDD，並保存可稽核證據。

## 建議下一步

### Step 1：完成本機 MVP 核心回合

- 完成星火決策、正式進度／危機套用與下一回合
- 完成結局條件、Mock storyteller fallback 與三玩家 E2E
- 建立 PostgreSQL repository ADR、schema 與 migrations
- 補齊 session expiry／revoke／reassign

### Step 2：通過 AWS 部署前關卡

- 確認最終 AWS 帳號、account plan、credits、Budget、principal 與 Region
- 取得 FastAPI＋private PostgreSQL 的講師等價性確認
- 完成 VPC、EC2、RDS、Bedrock 逐項估價與清理計畫
- 定義最小權限 app role、Security Group 與 SSM 邊界

### Step 3：開始共演計劃 Tier 0 實作

- 建立 VPC 與 subnet
- 建立 EC2 Web／API monolith
- 建立 private PostgreSQL 資料層
- 串接共演計劃與資料層、Amazon Bedrock
- 保存截圖並更新檢核清單

## 完成定義

一個階段完成時，必須同時具備：

- AWS 上可驗證的實作
- GitHub 中可閱讀的文件
- 對應截圖或 Demo 證據
- 已更新的檢核清單
- 可向講師說明的架構理由
