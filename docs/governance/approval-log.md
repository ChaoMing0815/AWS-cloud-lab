# 產品與實作核准紀錄

- 狀態：Active
- Owner：專題使用者
- Source of Truth：是，僅記錄已核准補充決策
- 最後檢視：2026-08-27

## 使用原則

本紀錄不複製正式 MVP Spec。若決策只是確認既有規格，標示「既有規格確認」；只有新增細節才標示「補充」。後續變更必須新增紀錄，不得靜默改寫舊決策。

## 2026-08-09 Web App 流程 Grill

| 決策 | 類型 | 核准內容 | 影響 |
| --- | --- | --- | --- |
| 房主身分 | 補充 | 房主是建房發起人，也是 3–5 位玩家之一；建房時同時取得 Host／Player 身份。人工 GM／DM 不存在，故事主持交由 LLM。 | Create room、Lobby 人數、session、E2E |
| 教學 Demo | 補充 | 保留首頁次要入口；固定 Mock、虛擬玩家、不呼叫正式 API／LLM／DB、不建立正式 session、不保存進度。 | Router、Demo composition、產品標示 |
| 跨裝置重新指派 | 既有規格＋補充 | 仍由房主核准；使用 10 分鐘一次性轉移碼，成功後撤銷舊 session。 | Session、audit、負面測試 |
| 房間與 session 期限 | 既有規格＋補充 | 進行中房間最後活動後 7 天到期；完成房間自結局後保留 7 天；session 不晚於房間到期，房主可提前永久刪除。 | Persistence、cleanup、UX |
| 世界草稿生成 | 既有規格確認 | 可完全手動或由 3–5 關鍵字生成；每房最多首次生成＋重新生成一次；失敗保留輸入，可重試或改手動，確認前不得進 Lobby。 | LLM contract、成本 UI |
| 回合敘事失敗 | 既有規格確認＋補充 | 自動重試一次；仍失敗後房主可手動重試一次或使用 deterministic fallback。Fallback 不改 canonical state；記錄 model、latency、token、retry、fallback 與估計成本，不記錄憑證。 | Storyteller、observability、QA |

核准方式：使用者於對話中逐項確認；Grill 進度 `6／6` 完成。

## 2026-08-11 Session lifecycle observable contract

| 決策 | 類型 | 核准內容 | 影響 |
| --- | --- | --- | --- |
| 活動與期限 | 補充 | 成功的加入、玩家行動、星火、回合結算與房主 mutation 延長對應 room／actor session；GET、polling、拒絕及失敗操作不延長。 | Expiry、activity refresh、負面測試 |
| 過期錯誤 | 補充 | 過期 read 回 `SESSION_NOT_FOUND`；mutation 回對應 session-required 錯誤，且不先洩漏 CSRF／version 細節。 | API、authorization、UX |
| 新舊轉移碼 | 補充 | 同一 Player 發行新 transfer code 時，舊未使用 code 立即失效。 | Repository、replay、concurrency |
| 房間狀態 | 補充 | DRAFT／LOBBY／進行中／已滿房可轉移既有 Player；完成後 7 天保留期內允許唯讀轉移；過期房禁止發碼與兌換。 | Transfer eligibility、ending UX |
| 房主的 Player | 補充 | 房主轉移自己的 Player 時只撤銷 Player session；原裝置 Host session 保留，UI 必須提示 Host 權限未移轉。 | Session rotation、UI、安全提示 |

核准方式：使用者先核准前三項，再於說明取捨後核准後兩項；五項均已完成核准。

## 2026-08-26 Tier 3 交付順序與安全 gate

| 決策 | 類型 | 核准內容 | 影響 |
| --- | --- | --- | --- |
| Tier 3 先於 Tier 2 | 交付順序補充 | 先完成 current monolith 的 Docker／ECR／GitHub OIDC／SSM 自動部署垂直切片，再以已驗證 pipeline 推進 Tier 2 queue／worker／data 拆分。Tier 2 與 Tier 3 仍是不同層面的能力，不改變累積演進關係。 | Gantt、CURRENT、Tier 2／3 task routing |
| 平行分支邊界 | 治理補充 | Storyteller 品質與 Tier 3 delivery 使用隔離 worktree／branch；只有整合 task 能修改 protected milestone 文件、擴張 allowed paths 與合併分支。 | work boundaries、merge gate、context management |
| PR 與 production release 分離 | 安全補充 | PR／`main` push 只執行 CI；production release 僅能以 `workflow_dispatch`、GitHub `production` environment 人工批准與 exact previous digest 啟動。合併 `main` 不等於授權 image push、SSM 或 production deploy。 | GitHub Actions、OIDC、T3B change envelope |
| Runtime-only image | 安全補充 | Python image 只作 builder；final 使用 digest-pinned Debian slim，移除 `pip`／`setuptools`，固定 `msgpack==1.2.1`。Trivy 必須維持 HIGH／CRITICAL fail-closed，不使用 ignore、VEX、skip 或降低 severity。 | Dockerfile、dependency policy、container scan |

核准方式：使用者於對話中核准先完成 Tier 3、自動整合 PR #8，以及合併後收斂決策與交接文件；production release 仍保留為下一個獨立 bounded batch。

## 2026-08-27 Tier 3 首次 production release與失敗後處置

| 決策 | 類型 | 核准內容 | 影響 |
| --- | --- | --- | --- |
| 首次T3B envelope | Production核准 | 核准 exact main `0add833c10414b1b51cb4733b12b669bdb04f85b`、`legacy-bootstrap`、空白previous digest與expected legacy release `tier1-20260825-4a51e0e`的完整自動鏈；仍須通過GitHub `production` environment人工gate。 | GitHub Actions、OIDC、ECR、SSM release |
| Scan fail-closed處置 | 安全補充 | ARM64 image成功push後，Trivy因amd64 runner平台選擇錯誤而停止；SSM step為skipped。禁止re-run舊SHA或手動執行SSM，必須先test-first明確指定`linux/arm64`，合併後以新exact SHA重新核准。 | Workflow contract、T3B retry boundary、production安全 |
| 平行Tier 2 bounded切片 | 交付順序補充 | Tier 3修正期間可平行建立PostgreSQL story-job durable adapter／migration contract；不得接入現行request flow、SQS或AWS，也不得改變玩家可見行為。 | Tier 2 branch boundary、Data contract、後續SQS接線 |
| 第二次T3B envelope | Production核准 | 核准 exact main `d81e4d7313d42bdec503305d588e782d6272c8f9`的`legacy-bootstrap`；previous digest空白，expected legacy release維持`tier1-20260825-4a51e0e`。 | GitHub Actions、ECR exact digest、SSM release |
| Migration fail-closed處置 | 安全補充 | 第二次run的scan通過，但container migration因缺少host RDS CA mount而在mutation前停止；不得降低TLS或re-run同SHA。修正採canonical instance gate、Document／driver雙重CA preflight與三個runtime路徑readonly bind，之後必須以新SHA重新核准。 | TLS verify-full、SSM Document、container runtime、T3B retry boundary |

核准方式：使用者於對話中先核准首次T3B，失敗後另核准platform修正，並要求整合文件後同步續推Tier 3與Tier 2兩個隔離task。
