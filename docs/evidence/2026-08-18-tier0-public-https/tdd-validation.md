# Tier 0 public HTTPS deployment-readiness 驗證摘要

- Scope／risk／upstream：R3；依已於 2026-08-18 核准的 Batch 6A envelope，為既有 public EC2 準備 direct IP HTTPS、ACME bootstrap、short-lived certificate renewal 與 fail-closed rollback；AWS 尚未公開。
- Baseline：Backend `292 passed, 8 skipped`；Frontend 未變更，沿用並於 merge gate 重跑。
- Red：`fd831b5`；7 個 targeted cases 因 public Nginx、Certbot timer、enable／renew／rollback assets 尚不存在而失敗。
- Green：`554a37f`；加入固定 public IP Nginx、ACME-only HTTP bootstrap、Certbot `5.4.0` short-lived flow、12 小時 renewal timer、production env 與 staging rollback。
- Boundary hardening：`334cdd4`；實際執行 global／private／loopback／documentation／malformed IPv4 cases，外部工作前 fail closed。
- Targeted／affected verification：public HTTPS 與既有 runtime／staging／rollback／internet gates `33 passed`；三支 shell scripts `bash -n` 通過。
- Full regression：Backend `300 passed, 8 skipped`；Frontend `80 passed`；只有既知 Starlette deprecation warning。
- Negative boundary：HTTP bootstrap 除 ACME challenge 外固定 `404`；production HTTP 只 redirect 到渲染後固定 IP；`22`／`8000`／`8080` 不由 scripts 開放；不含 AWS CLI、DB secret 或 password。
- Sensitivity：bootstrap `404→200` 與 global-IP predicate 反轉皆被 targeted tests 攔截；兩個 mutation 均已還原。
- Rollback：停用 public Nginx／renew timer，原子還原先前 runtime env，重啟並驗證 loopback staging readiness 後才刪除 certificate lineage。
- Artifact：修正版 local release `tier0-20260818-7b89e60` 已建立，`co-story.tar.gz` SHA-256 verification 為 `OK`；位於 Git-ignore `outputs/`，尚未部署。
- Residual risk：尚未在 AL2023 實機驗證 Certbot／Nginx／systemd、未聯絡 Let's Encrypt、未公開 EC2、未做 Browser certificate／cookie 驗證；Batch 6A 已核准，仍須逐步執行並保留停止點。

## 部署前最小權限修正

- Console／SSM preflight 證實現行 internal staging 已完成 migration bootstrap 權限清理；原 `install_staging.sh` 仍要求 master-secret ARN，不可用於後續 release update。
- Red：新增 update installer contract 後，因缺少 `install_release_update.sh` 與 bundle entry 正確失敗。
- Green：新增只沿用既有 `/etc/co-story/database.env` 的 update installer；只驗證 `root:co-story:640` metadata，不讀取內容、不要求 master／application secret ARN，並保留 activation rollback 與未啟用 release cleanup。
- 受影響 release／HTTPS／rollback suite：`23 passed`；shell syntax 通過。
- 代表性 sensitivity：暫時注入 `MASTER_SECRET` 字樣後，安全測試如預期失敗；移除 mutation 後重新全綠。
- 完整 Backend regression 的既有全綠基準仍為 `300 passed, 8 skipped`。本次誤用未安裝專案依賴的系統 Python 時只在 collection 階段回報缺少 `fastapi`／`psycopg`，不列為程式 regression 結果。

## Batch 6A.1 AWS 結果

- 使用者於 2026-08-18 明確核准 Batch 6A.1；只在 Console 開啟的 SSM Session 執行兩次 exact-object `aws s3 cp`，讀取 archive 與 checksum，沒有 list／recursive／sync／put／delete。
- `co-story.tar.gz: OK`；installer 由已驗證 archive 取出，未執行 S3 中的獨立 installer object。
- `release update installed; internal staging verified`。
- `/opt/co-story/current` 指向 `tier0-20260818-7b89e60`；application 與 staging Nginx 均為 `active`；loopback readiness HTTP `200`。
- 未重新開啟 migration bootstrap policy、未讀 master secret、未新增 AWS resource 或固定費用。尚未申請 certificate 或公開網站。

## Batch 6A AWS activation 結果

- Enable script 完成 Let's Encrypt staging／production short-lived IP certificate、certificate SAN／expiry check 與 renewal dry-run，回報 `public HTTPS enabled`。
- `co-story.service`、`co-story-nginx-public.service` 與 `co-story-certbot-renew.timer` 均為 `active`。
- EC2 內以 current public IPv4 對 loopback resolve 的 HTTPS readiness 回傳 HTTP `200`。
- Runtime 已切換 production、Secure cookie、固定 current public IPv4 allowed host／origin、Nova Lite 與 Guardrail version `1`；尚未執行真實模型 invocation。
- 未新增 Route 53、ACM、CloudFront、ALB、EIP、NAT、IAM 或固定月費 resource。尚待外部 Browser certificate／homepage 與負面 port／host／origin 驗證。

## Batch 6A 外部與負面驗證

- 一般 Browser 對 public IPv4 開啟 landing page，沒有 certificate warning；Co-Story landing page 可見。
- 明確輸入 HTTP 後自動 redirect 至 HTTPS，landing page 維持可見。
- Public `8000` 與 `8080` 均無法連線；`22` 由未變更的 CloudFormation／Security Group boundary 保持未開放。
- Production live HTTP `200`；錯誤 Host HTTP `400`；錯誤 Origin 的 unsafe request HTTP `403`；HSTS、CSP、`nosniff` 與 same-origin referrer policy 均存在。
- 使用者提供的原始 Browser 截圖含完整 public IPv4，只作即時驗證，不直接入庫；正式 evidence 須先遮罩網址列。
- Batch 6A 全部正面／負面 gate 通過，可於 2026-08-18 關閉。
