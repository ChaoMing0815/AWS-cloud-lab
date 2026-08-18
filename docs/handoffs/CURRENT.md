# CURRENT：目前工作交接

- 更新日期：2026-08-18
- 近期交付目標：2026-08-24 第一次報告前完成 Tier 0 AWS 公開試玩、去識別化證據與成本檢查；甘特圖 M3 `2026-08-20` 保留為內部提前完成目標。
- Branch：`codex/tier0-bedrock-guardrail`（從同步後的 `main` 建立；尚未 push／merge）
- Git checkpoint：公開模式 release update 修正 `27bebe2`；世界生成 schema／cache 修正 `d9c8f4e`
- 最後全綠功能基準：`27bebe2`（公開模式更新保留 active edge，edge 驗證失敗時恢復上一版）
- Regression：Backend `306 passed, 8 skipped`；Frontend `80 passed`（2026-08-18 重跑）
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
- Public release 已更新為 `tier0-20260818-27bebe2`：Batch 7.1R 只讀取 exact archive／checksum，驗證 checksum 後從 archive 取出 update installer；未重新取得 master secret。`co-story.service` 與 `co-story-nginx-public.service` active、staging inactive，`/opt/co-story/current` 指向該 release，公開 readiness HTTP `200`，首頁 `Cache-Control: no-store`。
- EC2 service restart persistence 已實機驗證：經正式 API 建立測試房間後，重啟 `co-story.service`，兩個 services 回到 active、readiness HTTP `200`，同一 session 讀回相同 room／status／version；測試房間以 API `204` 刪除，四個 `/tmp` session／JSON 暫存檔亦已清除。8/16 原訂 EC2／SSM／migration／restart persistence 成果完成。
- 實機安裝除錯已回饋到 tests 與 release tooling：包含 binary psycopg、bounded readiness retry、安全的既有 DB role rotate、symlink target 驗證，以及 Nginx journal／runtime write path。
- Guardrail `co-story-tier0-safety` 為 `Ready`：Standard filters、APAC cross-Region profile、EMAIL／PHONE Mask；固定 version `1` 已發布。`co-story-tier0-compute` 已以單一 `AppRole Modify / Replacement=False` change set 更新為 exact Nova Lite＋Guardrail v1 policy，stack 為 `UPDATE_COMPLETE`。
- AppRole Console inventory 保留 SSM、artifact 與 runtime-secret policies，沒有 Bedrock／Administrator Full Access；Policy Simulator 已驗證 exact Nova Lite＋Guardrail v1 為 `Allowed`、相同 model＋Guardrail v2 為 `Denied`。IAM Console 未顯示 Access Analyzer policy validation pane，因此未宣稱完成該項檢查；全程未使用 AWS CLI。
- Batch 6A 已完成：Let's Encrypt short-lived IP certificate、production runtime、public Nginx 與 renewal timer active；Browser 無 certificate warning、landing page 可見、HTTP→HTTPS，public `8000/8080` 不可達，bad Host／Origin 與 security headers 均符合。尚未完成真實 Bedrock／三玩家 smoke，因此仍不得宣稱 Tier 0 AWS 垂直切片完成。
- 使用者決定後續維持 AWS Free plan／credits 與最低成本，現階段不購買網域。既有 EC2＋Let's Encrypt short-lived IP certificate 路徑已完成，新增 AWS resource 為 0；未建立 CloudFront／Route 53／ACM／ALB。
- Batch 6A／6A.1 已完成並關閉；release `tier0-20260818-7b89e60` 通過 checksum、internal activation、可信任 public HTTPS 與正負 boundary。Batch 7 已核准並完成 exactly 3 次 SDK `ApplyGuardrail`：benign allow、harmful block、synthetic EMAIL／PHONE mask 全符合；content／sensitive 各 3 units，估算 `US$0.00075`。首次真實世界生成已送達 Nova Lite 並產生 input／output token metrics，但應用因模型 JSON 草稿不合 schema 回傳 `503`；生成額度剩 1 次，不得在修正版部署前重試。
- 世界生成 schema／cache 修正 `d9c8f4e` 已包含在正式 release。首次更新因舊 installer 以 `localhost` 驗證 public runtime 而失敗並乾淨回滾；TDD 修正 `27bebe2` 會保留 active public／staging edge 並在 edge 失敗時恢復上一版。第一次安裝 `27bebe2` 又因下載步驟留下的 caller `umask 0077` 令新 venv 無法由 `co-story` 執行，仍在切換前乾淨回滾；隔離 root subshell 使用 `umask 022` 後部署成功。兩次失敗均未中斷舊版公開服務。
- Batch 7.1／7.1R 已完成並關閉：只沿用既有 private S3／SSM，不新增 resource、IAM、RDS／TLS／DNS 變更或模型 invocation。Batch 7.2 隨後核准並完成一次公開 HTTPS 真實世界生成：Nova Lite 回傳符合 schema 的繁體中文草稿，五個 canonical 欄位自動填入、無錯誤，生成次數由 canonical `2` 變為 `1`。先前失敗呼叫未持久化扣次，重新載入後恢復為 `2`，證明交易 rollback 邊界有效。
- Batch 8A 三玩家公開單回合 smoke 已完成：三個獨立 Browser sessions 加入同房、建立角色、同步三個 action、擲骰與各自星火決策；房主以 exactly 1 次真實 Nova Lite 敘事結算後進入第 2 回合，正式進度 `4（13%）`、危機 `2（7%）`、AI 敘事與三個 sessions 同步。三個頁面重新整理後完整讀回狀態，private RDS refresh gate 通過。重新整理時短暫閃回 Landing 是待改善的 loading-shell 視覺問題，不是資料遺失。
- Batch 8A 後 Cost Explorer 唯讀檢查顯示 Total、Amazon Bedrock、EC2、RDS 與其他服務目前均為 `0`；帳務可能延遲入帳，後續成本證據須保留此限制，不將即時 `0` 解讀為永久零成本。
- Prompt Attack filter 雖已設為 High，但目前 Converse request 尚未以 `guardContent` 標示 user-controlled prompt；依 AWS 規則不得宣稱 prompt injection 防護已充分啟用。第一輪 smoke 後、首次公開展示前安排小型 TDD hardening：加入 `guardContent`／query qualifier、benign 與 injection 代表性測試，不變更模型、IAM 或 Guardrail version。
- 推進原則：甘特圖是先後與風險參考，不是速度上限。當日預定成果、驗證與必要文件均完成後，可提前推進下一個最小切片或做不擴張成本／權限／產品範圍的小幅優化；不得跳過 Tier gate、TDD、bounded batch、成本、安全或證據關卡。
- 專案文件入口已收斂：根目錄 `README.md` 只保留產品、架構、執行方式與核心文件入口；完整文件索引位於 `docs/README.md`，證據保存規則位於 `docs/evidence/README.md`。
- `codex/session-lifecycle` 已 push 並透過 PR `#1` 合併到 `main`；三個更早的 remote feature branches 與該 branch 均已被 `main` 包含，remote branch 指標清理屬可選 Git housekeeping，不阻塞 AWS 進度。

## Next

```text
Batch 6A／6A.1 public HTTPS 與正負 boundary 已完成
→ Batch 7 已明確核准
→ SSM 內以既有 SDK exactly 3 次 ApplyGuardrail 驗證 allow／block／synthetic PII mask
→ `tier0-20260818-27bebe2` 已部署並通過 HTTPS／cache release gate
→ Batch 7.2 真實世界生成已成功，尚餘 1 次但不得為重複驗證而使用
→ Batch 8A 公開 HTTPS 三玩家單回合、真實 storyteller 與 private RDS refresh 已完成
→ Batch 後 Cost Explorer 目前全為 0；完成去識別化證據與第一份報告
→ 依清理計畫停止或刪除持續計費資源，保留程式碼、IaC 與去識別化證據
→ 再進入 Tier 1 可觀測性最小切片
```

新對話的第一步：確認 `codex/tier0-bedrock-guardrail` 工作樹與 `27bebe2`，再依 `operate-aws-final-project` 與本文件，從 **bounded 真實世界生成 smoke approval** 接續。仍採 Console-first，每次只做一個可驗證小步驟，且未核准新的 AWS CLI batch 前仍禁止 AWS CLI。

## Residual risks

- Public Web／TLS、真實世界生成、三玩家公開單回合、真實 storyteller、private RDS refresh 與 Batch 後 Cost Explorer 檢查均完成；尚待去識別化 evidence。進行中的 smoke room 依 SSOT 最後活動後 7 天到期；目前永久刪除 UI 只在結局後提供，不為清理而額外執行五回合模型呼叫。
- Page bootstrap 在 canonical session 載入前會短暫顯示 Landing，狀態隨後正確恢復；列入第一輪 smoke 後 UI backlog，不阻塞 Tier 0。
- Release updater 尚未在 script 內固定安全的安裝 `umask`；本次以 root subshell `umask 022` 成功部署，下一個 release 前須以 TDD 將此不變量寫入 installer，避免 caller shell 設定再次造成 service EXEC permission failure。
- IAM Access Analyzer basic policy validation 未在 Console 顯示；CloudFormation、R3 tests、安全 review 與正負 Policy Simulator 已通過，但此項仍記為未執行。
- 尚無自有網域；Route 53 註冊不是免費項目且 domain registration 不能使用 AWS credits。建議的 direct IP certificate 只有約 160 小時效期，必須證明自動續期；EC2 stop/start 若改變 public IP，URL、certificate 與 application allowlist 都需重建。CloudFront global path／HTTP origin trade-off 只作備選。
- 尚未完成 AWS 三玩家核心流程與公開路徑 smoke test；EC2 service restart persistence 已通過。
- Idempotency store 仍是 process memory，不宣稱 multi-process exactly-once。
- EC2 與 RDS 持續運行會消耗 credits；artifact objects 依 7 日 lifecycle 自動到期，但 stack／bucket 不會自動刪除。
- 原始截圖若仍位於 macOS TemporaryItems，尚未算 repo evidence；入庫前必須去除 account ID、ARN、instance／subnet／SG IDs、endpoint、secret ARN 與 bucket 隨機 suffix。
