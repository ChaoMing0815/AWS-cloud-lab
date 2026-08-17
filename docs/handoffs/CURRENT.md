# CURRENT：目前工作交接

- 更新日期：2026-08-17
- 近期交付目標：2026-08-24 第一次報告前完成 Tier 0 AWS 公開試玩、去識別化證據與成本檢查；甘特圖 M3 `2026-08-20` 保留為內部提前完成目標。
- Branch：`codex/tier0-bedrock-guardrail`（從同步後的 `main` 建立；尚未 push／merge）
- Git checkpoint：Batch 5A functional tip `f63c488`；validation manifest `6ed5c0c`
- 最後全綠功能基準：`f63c488`（固定 Nova Lite＋Guardrail v1 bounded runtime IAM）
- Regression：Backend `292 passed, 8 skipped`（2026-08-17 重跑）；Frontend `80 passed`（未受本批影響，沿用最近全綠基準）
- AWS：Tokyo `ap-northeast-1` 已有 IAM、network、private RDS、EC2＋SSM、private artifacts、runtime secrets、Guardrail v1 與 bounded Bedrock runtime IAM；無 NAT／EIP／SSH
- 操作邊界：Console-first；曾在使用者逐批明確核准後，於 EC2 的 SSM Session 內執行 exact-prefix S3 download 與安裝指令。未修改 `~/.aws`、憑證或 Keychain。

## Current

- 本機 MVP P0 release gate 已全綠：正式入口、三玩家回合、結局、PostgreSQL persistence、LLM recovery、polling 與 session lifecycle。
- Network stack 已部署：VPC `10.20.0.0/16`、1 個 public app subnet、2 個 private DB subnets、private local-only route、無 NAT／EIP；DB `5432` 只接受 App Security Group。
- RDS stack `co-story-tier0-rds` 已部署：PostgreSQL `18.3`、Single-AZ `db.t4g.micro`、20 GiB gp2、private-only、加密、RDS-managed master secret，狀態 `Available`。
- Compute stack `co-story-tier0-compute` 已部署：AL2023 ARM64 `t4g.micro`、8 GiB encrypted gp3、IMDSv2 required、無 Key Pair／SSH；EC2 checks passed，SSM managed node Online。
- Artifact stack `co-story-tier0-artifacts` 已部署：generated-name private S3 bucket、Block Public Access、SSE-S3、BucketOwnerEnforced、TLS-only、`releases/` 7 日到期；AppRole 只有 exact-prefix list／read。
- Runtime secrets stack `co-story-tier0-runtime-secrets` 已部署：application DB secret 與永久 exact-secret read policy 保留。DB bootstrap／migration 完成後，`EnableMigrationBootstrapAccess=false` 的 change set 只移除 temporary master-secret policy，stack 已 `UPDATE_COMPLETE`。
- AWS private RDS 已完成 `co_story_app` restricted role bootstrap 與 migration；role 不具 superuser／createdb／createrole／replication／bypassrls，應用 DSN 使用 `verify-full`。
- Internal staging release `tier0-20260816-b028569` 已在 EC2 啟用：`co-story.service` 與 `co-story-nginx-staging.service` 均為 active，`/opt/co-story/current` 指向該 release，`http://127.0.0.1:8080/api/v1/ready` 回傳 HTTP `200`。
- EC2 service restart persistence 已實機驗證：經正式 API 建立測試房間後，重啟 `co-story.service`，兩個 services 回到 active、readiness HTTP `200`，同一 session 讀回相同 room／status／version；測試房間以 API `204` 刪除，四個 `/tmp` session／JSON 暫存檔亦已清除。8/16 原訂 EC2／SSM／migration／restart persistence 成果完成。
- 實機安裝除錯已回饋到 tests 與 release tooling：包含 binary psycopg、bounded readiness retry、安全的既有 DB role rotate、symlink target 驗證，以及 Nginx journal／runtime write path。
- Guardrail `co-story-tier0-safety` 為 `Ready`：Standard filters、APAC cross-Region profile、EMAIL／PHONE Mask；固定 version `1` 已發布。`co-story-tier0-compute` 已以單一 `AppRole Modify / Replacement=False` change set 更新為 exact Nova Lite＋Guardrail v1 policy，stack 為 `UPDATE_COMPLETE`。
- AppRole Console inventory 保留 SSM、artifact 與 runtime-secret policies，沒有 Bedrock／Administrator Full Access；Policy Simulator 已驗證 exact Nova Lite＋Guardrail v1 為 `Allowed`、相同 model＋Guardrail v2 為 `Denied`。IAM Console 未顯示 Access Analyzer policy validation pane，因此未宣稱完成該項檢查；全程未使用 AWS CLI。
- 目前 runtime **只在 EC2 loopback internal staging**，尚未公開提供 Web／TLS；不得宣稱 Tier 0 AWS 垂直切片完成。
- 使用者決定後續維持 AWS Free plan／credits 與最低成本，現階段不購買網域。2026-08-17 比較結果建議以既有 EC2＋Let's Encrypt short-lived IP certificate 完成端到端 HTTPS，新增 AWS resource 為 0；CloudFront pay-as-you-go default domain 保留為備選。Batch 6A 尚未核准，未建立 CloudFront／Route 53／ACM／ALB。
- 推進原則：甘特圖是先後與風險參考，不是速度上限。當日預定成果、驗證與必要文件均完成後，可提前推進下一個最小切片或做不擴張成本／權限／產品範圍的小幅優化；不得跳過 Tier gate、TDD、bounded batch、成本、安全或證據關卡。
- 專案文件入口已收斂：根目錄 `README.md` 只保留產品、架構、執行方式與核心文件入口；完整文件索引位於 `docs/README.md`，證據保存規則位於 `docs/evidence/README.md`。
- `codex/session-lifecycle` 已 push 並透過 PR `#1` 合併到 `main`；三個更早的 remote feature branches 與該 branch 均已被 `main` 包含，remote branch 指標清理屬可選 Git housekeeping，不阻塞 AWS 進度。

## Next

```text
取得 Batch 6A（Direct EC2＋Let's Encrypt IP certificate）明確核准
→ 先完成 local R3 TDD、renewal／rollback 與 production packaging
→ 依 Console-first＋SSM 小步驟申請 certificate 並啟用 production runtime
→ 驗證公開 Web、private RDS read/write、一次真實 Bedrock 故事生成
→ 完成三玩家 AWS smoke test、成本檢查、證據收斂與第一份報告
→ 依清理計畫停止或刪除持續計費資源，保留程式碼、IaC 與去識別化證據
→ 再進入 Tier 1 可觀測性最小切片
```

新對話的第一步：確認 `codex/tier0-bedrock-guardrail` 工作樹與 Batch 5A commits，再依 `operate-aws-final-project`、本文件與 `docs/architecture/tier0-aws-change-envelope.md`，從 **Batch 6A Direct EC2 public HTTPS 核准關卡** 接續。仍採 Console-first，每次只做一個可驗證小步驟；除非使用者明確核准 Batch 6A，禁止 production exposure／外部 CA 寫入；未核准新的 AWS CLI batch 前仍禁止 AWS CLI。

## Residual risks

- 尚無 public Web／TLS boundary，也沒有對外可玩的 URL。
- 尚未完成真實 Bedrock invocation 與 Guardrail 功能層 allow／block／PII mask 測試；目前只有 IAM allow／deny simulation，不能替代真實模型驗證。
- IAM Access Analyzer basic policy validation 未在 Console 顯示；CloudFormation、R3 tests、安全 review 與正負 Policy Simulator 已通過，但此項仍記為未執行。
- 尚無自有網域；Route 53 註冊不是免費項目且 domain registration 不能使用 AWS credits。建議的 direct IP certificate 只有約 160 小時效期，必須證明自動續期；EC2 stop/start 若改變 public IP，URL、certificate 與 application allowlist 都需重建。CloudFront global path／HTTP origin trade-off 只作備選。
- 尚未完成 AWS 三玩家核心流程與公開路徑 smoke test；EC2 service restart persistence 已通過。
- Idempotency store 仍是 process memory，不宣稱 multi-process exactly-once。
- EC2 與 RDS 持續運行會消耗 credits；artifact objects 依 7 日 lifecycle 自動到期，但 stack／bucket 不會自動刪除。
- 原始截圖若仍位於 macOS TemporaryItems，尚未算 repo evidence；入庫前必須去除 account ID、ARN、instance／subnet／SG IDs、endpoint、secret ARN 與 bucket 隨機 suffix。
