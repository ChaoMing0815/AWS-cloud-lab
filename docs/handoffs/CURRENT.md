# CURRENT：目前工作交接

- 更新日期：2026-08-16
- Branch：`codex/session-lifecycle`
- 最後全綠功能基準：`b028569`（staging Nginx runtime write boundary）
- Regression：Backend `290 passed, 8 skipped`（2026-08-16 重跑）；Frontend `80 passed`（未受本批影響，沿用最近全綠基準）
- AWS：Tokyo `ap-northeast-1` 已有 IAM、network、private RDS、EC2＋SSM、private artifacts、runtime secrets 與 Guardrail；無 NAT／EIP／SSH
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
- Guardrail `co-story-tier0-safety` 為 `Ready`：Standard filters、APAC cross-Region profile、EMAIL／PHONE Mask；尚未發布固定 version、Test 或執行真實 model invocation。
- 目前 runtime **只在 EC2 loopback internal staging**，尚未公開提供 Web／TLS；不得宣稱 Tier 0 AWS 垂直切片完成。
- 專案文件入口已收斂：根目錄 `README.md` 只保留產品、架構、執行方式與核心文件入口；完整文件索引位於 `docs/README.md`，證據保存規則位於 `docs/evidence/README.md`。

## Next

```text
結束操作中的 SSM Session
→ Console 唯讀確認 Guardrail draft／version 狀態與 Nova Lite 的精確 model／inference profile 識別
→ 發布並驗證固定 Guardrail version，建立 exact model／Guardrail AppRole policy
→ 規劃並審查 public Web＋TLS boundary，再啟用 production runtime
→ 驗證公開 Web、private RDS read/write、一次真實 Bedrock 故事生成
→ 完成三玩家 AWS smoke test、成本檢查、證據收斂與第一份報告
```

明日新對話的第一步：依 `operate-aws-final-project`、本文件與 `docs/architecture/tier0-aws-change-envelope.md`，從 **Batch 5 Guardrail 固定版本與 Bedrock bounded IAM** 接續；仍採 Console-first，每次只做一個可驗證小步驟。除非使用者另行核准新的 bounded batch，禁止 AWS CLI。

## Residual risks

- 尚無 public Web／TLS boundary，也沒有對外可玩的 URL。
- 尚未完成真實 Bedrock invocation、固定 Guardrail version 與 bounded allow／block／PII 測試。
- 尚未完成 AWS 三玩家核心流程與公開路徑 smoke test；EC2 service restart persistence 已通過。
- Idempotency store 仍是 process memory，不宣稱 multi-process exactly-once。
- EC2 與 RDS 持續運行會消耗 credits；artifact objects 依 7 日 lifecycle 自動到期，但 stack／bucket 不會自動刪除。
- 原始截圖若仍位於 macOS TemporaryItems，尚未算 repo evidence；入庫前必須去除 account ID、ARN、instance／subnet／SG IDs、endpoint、secret ARN 與 bucket 隨機 suffix。
