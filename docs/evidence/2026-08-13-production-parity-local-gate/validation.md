# Production-parity local gate 驗證摘要

- 範圍／風險：R2；本機 MVP 完成後的 AWS 串接準備門檻，不含 AWS 寫入。
- 乾淨 runtime：temporary Python 3.13 virtualenv 依 `requirements-prod.txt` 成功安裝，並可 import `app.main`、`boto3`、`botocore`。
- Production process：以 placeholder PostgreSQL／Bedrock 設定在 loopback 啟動；未呼叫 AWS 或 RDS。
- Health：`/api/v1/live` 回 `200`；故意不可用的 PostgreSQL `/api/v1/ready` 回 generic `503`，沒有回顯連線細節。
- Security：production 回應含 HSTS、CSP、`nosniff`、same-origin referrer 與 API `no-store`。
- Contracts：production dependencies、composition、health/static、internet release、migration readiness、runtime bundle、structured log 共 `54 passed`。
- Regression：Backend `239 passed, 8 skipped`；Frontend `80 passed`。
- Release assets：activate／rollback shell syntax 通過；tracked files 高訊號 AWS／private key／GitHub／Slack token scan 為空。
- Rollback／residual risk：本批未變更 production code、AWS 或部署環境；真實 RDS、Bedrock Guardrail、TLS reverse proxy 與 Linux／EC2 實測留給 Tier 0 deployment gate。
