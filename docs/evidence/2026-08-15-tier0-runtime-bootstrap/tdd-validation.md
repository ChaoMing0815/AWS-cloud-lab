# Tier 0 runtime bootstrap 驗證摘要

- Scope／risk／upstream source：Batch 4 application DB secret、暫時 master bootstrap 權限、restricted DB role 與 host secret file；R3 IAM／credential／migration。
- Baseline：既有 IAM／RDS／EC2 templates 與 runtime／migration contracts 全綠。
- Red commits：`bd7a8c0`（secret boundary）；`a8ca216`（private DB bootstrap）；`8a4b776`（staging release bundle）；`51e5165`（artifact scope）；`cc1b9a1`（private artifact boundary）。
- Green commits：`7efcec9`（generated secret＋conditional exact-resource policies）；`35b11c1`（DB role bootstrap＋protected environment file）；`99d160d`（verified staging install／activation）；`7b33cbd`（artifact scope restriction）；`a97b8f2`（private artifact CloudFormation）。
- Targeted verification：secret／IAM／RDS／EC2／artifact contracts `20 passed`；bootstrap／runtime／release／migration contracts 全綠；Bash syntax 全綠。
- Release artifact：`outputs/releases/tier0-20260815-7b33cbd/`，bundle 約 `120 KiB`、SHA-256 驗證成功，archive 只含 `backend/`、`ops/`、`web/`。
- Full regression：Backend `282 passed, 8 skipped`；Frontend 沿用未受影響的 `80 passed` 基準。
- Negative：拒絕非 `co_story_app` 或不完整 secret、unsafe endpoint／CA、environment newline injection；template 禁止 password 明文與 `Resource: *`。
- Boundary：DB role 固定 `NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS`；DSN 固定 `5432`、`co_story`、`sslmode=verify-full`。
- Sensitivity：bootstrap master resource 暫改 `*`、`database.env` 暫改 `0644`、Nginx staging listen 暫改 `0.0.0.0:8080`、S3 `RestrictPublicBuckets` 暫改 `false` 時，各自 contract 均正確失敗；全部立即還原並重跑全綠。
- Rollback：secrets Change Set 尚未 Execute；migration 後先將 conditional bootstrap access 更新為 `false`，schema forward-only、不自動 downgrade。
- Residual risk：尚未在 AL2023 EC2 實機安裝、連 private RDS、執行 migration 或驗證 restart persistence；artifact template 已完成但 Bucket 尚未建立，release bundle 尚未上傳。
