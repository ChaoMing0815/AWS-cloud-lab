# Tier 0 internal staging 部署驗證

## 範圍與風險

- 範圍：private deployment artifacts、runtime secrets、restricted PostgreSQL role、migration 與 EC2 internal staging runtime。
- 風險：R3（IAM、secret、database migration、runtime activation）。
- 上游：`docs/product/source-of-truth.md`、`docs/architecture/tier0-aws-change-envelope.md` 與已核准的 Batch 4／6 系列 bounded operations。
- 本紀錄不保存 account ID、完整 ARN、instance／subnet／Security Group ID、RDS endpoint、secret value 或 bucket 隨機 suffix。

## AWS 結果

- `co-story-tier0-artifacts`：`CREATE_COMPLETE`。
  - generated-name private S3 bucket。
  - Block Public Access、SSE-S3、BucketOwnerEnforced、TLS-only。
  - `releases/` objects 7 日到期；AppRole 僅能 list／read exact release prefix。
- `co-story-tier0-runtime-secrets`：初次 `CREATE_COMPLETE`，完成 migration 後更新為 `UPDATE_COMPLETE`。
  - application DB secret 與永久 exact-secret read policy 保留。
  - `EnableMigrationBootstrapAccess=false`；temporary master-secret read policy 已刪除。
- Private RDS：`co_story_app` restricted role bootstrap 與 schema migration 完成；沒有 superuser、createdb、createrole、replication 或 bypassrls。
- EC2 internal staging：
  - active release：`tier0-20260816-b028569`。
  - `co-story.service`：active。
  - `co-story-nginx-staging.service`：active。
  - internal endpoint `127.0.0.1:8080/api/v1/ready`：HTTP `200`。
  - staging Nginx 只監聽 loopback，尚未建立 public Web／TLS boundary。

## Bounded CLI 與憑證邊界

- AWS CLI 只在使用者對 release-specific Batch 明確核准後，於 EC2 的 SSM Session 內下載指定 S3 prefix。
- 操作只有 exact-prefix read／copy，沒有 S3 put、delete、bucket inventory 或其他帳號盤點。
- 安裝／驗證指令在同一受控 SSM shell 執行；未使用 SSH。
- 未修改 `~/.aws`、本機 credential、Keychain 或建立長期 Access Key。
- Release archive 在安裝前以 SHA-256 驗證，結果為 `OK`。

## 實機回饋與修正

- Production dependency 明確加入 binary psycopg，避免 AL2023 缺少 libpq wrapper。
- Readiness 改為 bounded retry，吸收首次安裝與 service startup 的合理延遲。
- 既有 PostgreSQL application role 重跑時只驗證安全 attributes 並 rotate password，不嘗試修改 `SUPERUSER` attribute。
- Activation 僅接受位於 releases directory 內的有效既有 symlink target；dangling／self-link 會被拒絕或移除。
- Staging Nginx 將 log 送至 journal，PID／proxy temp paths 限定在 systemd `RuntimeDirectory`，保留 `ProtectSystem=strict`。

## 驗證

- Backend regression：`290 passed, 8 skipped`；只有既有 Starlette deprecation warning。
- Release shell syntax 與相關 contract tests：全綠。
- Bundle checksum：`co-story.tar.gz: OK`。
- systemd：application 與 staging Nginx services 均為 active。
- Active symlink：解析至 `tier0-20260816-b028569` release directory。
- Internal readiness：HTTP `200`。
- Service restart persistence：
  - 重啟前：同一 session 讀回測試房間，room match `true`、status `DRAFT`、version `1`。
  - `co-story.service` restart 後：application／Nginx 均為 active，readiness HTTP `200`。
  - 重啟後：room／status／version match 均為 `true`，證明 room 與 session 可由 PostgreSQL 還原。
  - 收尾：測試房間以正式 API 刪除並回傳 HTTP `204`；cookie 與三份 JSON `/tmp` 檔案已清除。
- CloudFormation cleanup：只移除 migration bootstrap policy，stack `UPDATE_COMPLETE`。

## 成本、安全與停止點

- 本批未新增 NAT Gateway、Elastic IP、ALB、另一台 EC2 或另一個 RDS。
- 新增成本主要是 1 個 Secrets Manager secret，以及少量 S3 storage／requests；S3 release objects 有 7 日 lifecycle。
- EC2 與 RDS 繼續運行並消耗 credits；完成展示後仍須依清理計畫停用／刪除。
- Secret value、DSN、完整 identifiers 與 public endpoint 均未寫入 Git 或本證據。
- 本批在 internal readiness 與 temporary permission removal 完成後停止，沒有擴張至公開部署。

## 尚未完成

- Public Web／TLS boundary 與正式對外 URL。
- 固定 Guardrail version、exact Bedrock model policy 與真實故事生成。
- AWS 三玩家核心流程 smoke test 與最終成本檢查；service restart persistence 已完成。
- Console／SSM 原始截圖若要入庫，仍須逐張去識別化並加入 screenshot index。
