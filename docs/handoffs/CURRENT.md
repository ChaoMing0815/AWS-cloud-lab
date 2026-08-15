# CURRENT：目前工作交接

- 更新日期：2026-08-15
- Branch：`codex/session-lifecycle`
- 最後全綠功能基準：`a97b8f2`（private artifact boundary）
- Regression：Backend `282 passed, 8 skipped`；Frontend `80 passed`（未受本批影響，沿用最近全綠基準）
- AWS：IAM bootstrap、Tier 0 network、private RDS 與 EC2＋SSM management plane 已在 Tokyo 部署；無 NAT／EIP／SSH；全程無 AWS CLI

## Current

- 本機 MVP P0 release gate 已全綠：正式入口、三玩家回合、結局、PostgreSQL restart、LLM recovery、polling 與 session lifecycle。
- Transfer code 為 10 分鐘一次性 hash-only；redeem 原子 rotate Player session／CSRF 並撤銷舊 session。
- 房主轉移自己的 Player 時保留原 Host session；完成房在保留期可唯讀轉移。
- 房主永久刪除有原子 repository contract、204 與三 cookie 清除；刪後所有舊 session／transfer 不可用。
- Browser 已觀察 offline→reconnected、session-expired、completed 與 console 無未處理錯誤。
- 房主可輸入 3–5 個關鍵字生成兩次可編輯 WorldDraft；失敗與 replay 仍受 inference／idempotency 成本邊界限制。
- `BedrockStoryteller` 已完成 Converse、Guardrail、schema、canonical 結果 prompt 與安全錯誤分類；production 缺 Region／model／Guardrail／token ceiling 時拒絕啟動。
- Migration 為獨立、可重跑 command；readiness 同時驗證 PostgreSQL 與所有 schema migration version，Web boot 不會自動套用 migration。
- 到期房間 cleanup 以獨立 use case／repository bulk delete 實作：所有狀態的 `expires_at <= now` 均會刪除，demo `None` 與未到期房間保留；未連接 timer 或 Web boot。
- `requirements-prod.txt` 為精確 runtime lock，包含 `boto3`／`botocore`；開發依賴引用同一 lock。
- runtime bundle 採 Nginx loopback proxy、systemd non-root single worker 與 repo 外 environment／TLS；release 以 per-release `.venv`、candidate readiness 與 `mv -Tf` 原子切換，rollback 禁止 schema downgrade。
- API request log 為 JSON allowlist：僅含 server-generated request ID、method、純 path、status 與 latency；不得記錄 query、headers、cookies 或 body。
- 正式 `/rules` 提供唯讀的新手規則摘要，首頁與遊戲頁可開啟；不改變遊戲規則、session 或 API state。
- 預設 Mock 生成的 WorldDraft 可直接確認為 Lobby，不再因 `premise` 長度不足得到 `422`；HTTP 的 FastAPI `422` 會以安全的欄位級提示標示世界表單，草稿保持可編輯。
- 本機 MVP 為 **100%（AWS 串接準備完成）**：乾淨 production lock install／import、production live／ready fail-closed、security headers、release assets 與 tracked-file secret scan 已驗證；完整定義與停止規則見 `docs/qa/local-mvp-test-plan.md`。
- Tier 0 network CloudFormation 已部署：VPC `10.20.0.0/16`、1 public app subnet、2 private DB subnets、local-only private route 與 App／DB SG 均通過 Console 驗證。
- 2026-08-13 Batch 0 已確認 Free plan／credits／Budget／本月零成本、Organizations 缺席、IAM 安全基線、Tokyo `ap-northeast-1`、RDS／EC2／NAT／EIP／endpoint 零資源、default VPC `172.31.0.0/16` 與 CloudTrail onboarding 事件；證據見 [`docs/evidence/2026-08-13-tier0-batch0-console-inventory/`](../evidence/2026-08-13-tier0-batch0-console-inventory/inventory-summary.md)。
- `ming-dev` 已使用 `PowerUserAccess`＋專題前綴 IAM delegation，並保留 account／Organizations／購買／長期 key deny；Root bootstrap 後已登出，日常操作回到 MFA 的 `ming-dev`。
- 實機發現 SG 空 egress list 會產生 EC2 default allow-all；已用 localhost sink 修正 App／DB SG。Red `117bf3b`、Green `a78da19`，stack `UPDATE_COMPLETE`，Backend `247 passed, 8 skipped`。
- Tier 0 private RDS template 已完成本機 R3 TDD：RDS API PostgreSQL `18.3`、Single-AZ `db.t4g.micro`、20 GiB gp2、private-only、RDS-managed secret、Extended Support disabled；原始 Red `7d6cebd`、Green `58fb058`，engine version correction `7b01591`。
- Batch 2 已核准；`tier0-rds-20260814` change set 為 `CREATE_COMPLETE`／`AVAILABLE`，只有 `Database` 與 `DbSubnetGroup` 兩筆 `Add`。2026-08-14 暫停於 Execute 前，因此尚未開始 RDS 計費。
- 2026-08-15 第一次 RDS 執行因三個 network parameters 留空而 rollback；第二次發現 Console 版本描述 `18.3-R2` 不能直接作為 API `EngineVersion`。test-first 修正為 `18.3` 後第三次建立成功：stack／Database `CREATE_COMPLETE`、RDS `Available`、Internet access gateway disabled、加密、managed secret 與 DB SG boundary 均通過 Console 驗證。
- Batch 3 EC2＋SSM 已部署並驗證：AL2023 ARM64 `t4g.micro`、8 GiB encrypted gp3、CPU credits standard、IMDSv2-only、無 Key Pair／UserData／SSH；stack `CREATE_COMPLETE`、EC2 checks passed、SSM Online，Session Manager 實機為 `ssm-user`／`aarch64`／agent active。AppRole 目前只有 SSM core。
- Batch 4 secrets Change Set `tier0-runtime-secrets-20260815` 已建立但未執行：`CREATE_COMPLETE`／`AVAILABLE`，只有 application DB secret、exact app-secret read policy 與 conditional master-secret bootstrap policy 三筆 `Add`。為縮短 master secret 暫時權限的存續時間，須等 release bundle 完成後才 Execute。
- Batch 4 private DB bootstrap 已完成本機 R3 TDD：只讀兩個指定 secret ARN、固定建立／rotate `co_story_app`、禁止 superuser／createdb／createrole／replication／bypassrls、PostgreSQL `verify-full`，並以 `root:co-story` `0640` 原子寫入獨立 `database.env`；systemd web／candidate／migration units 均分離讀取此檔。
- staging release bundle 與 AL2023 install／activation 已完成本機 R3 TDD：Nginx 僅綁 `127.0.0.1:8080`、systemd non-root runtime、checksum-before-install、candidate readiness、first-deploy cleanup 與 previous-release rollback。最終 bundle 約 `120 KiB`，SHA-256 驗證成功，archive 只含 `backend/`、`ops/`、`web/`。
- `infra/cloudformation/tier0-deployment-artifacts.yaml` 已完成本機 TDD：generated-name private S3 bucket、四項 Block Public Access、SSE-S3、BucketOwnerEnforced、`releases/` 7 日到期、TLS-only policy，AppRole 只可 list／read exact prefix，沒有 put／delete。
- 使用者已核准短期 private S3 deployment artifact bucket，但明確要求目前先不建立；Bucket 尚未建立、bundle 尚未上傳，無 S3 資源或費用。

## Next

```text
使用者準備實際傳送時，再建立／審查 artifact Change Set 並以 Console 上傳已驗證 release bundle
→ Execute secrets Change Set，立即以 SSM Console bootstrap `co_story_app`、migration 與 internal staging runtime
→ 將 EnableMigrationBootstrapAccess 更新為 false 後，驗證 private RDS readiness 與 restart persistence；TLS／Bedrock 維持獨立後續邊界
```

本機 MVP 100% 不等於 Tier 0 AWS 已完成：真實 model／Guardrail、RDS readiness、TLS 與 AWS 驗證尚未執行。Residual risk：idempotency 仍是 process memory，不宣稱 multi-process exactly-once；release assets 與 DB bootstrap 尚未在 Linux VM／EC2 實機驗證；Bucket 尚未建立。
