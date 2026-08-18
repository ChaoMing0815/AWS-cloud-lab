# Tier 0 public HTTPS deployment-readiness 驗證摘要

- Scope／risk／upstream：R3；依 Batch 6A Proposed envelope，為既有 public EC2 準備 direct IP HTTPS、ACME bootstrap、short-lived certificate renewal 與 fail-closed rollback；不代表 Batch 已核准或 AWS 已公開。
- Baseline：Backend `292 passed, 8 skipped`；Frontend 未變更，沿用並於 merge gate 重跑。
- Red：`fd831b5`；7 個 targeted cases 因 public Nginx、Certbot timer、enable／renew／rollback assets 尚不存在而失敗。
- Green：`554a37f`；加入固定 public IP Nginx、ACME-only HTTP bootstrap、Certbot `5.4.0` short-lived flow、12 小時 renewal timer、production env 與 staging rollback。
- Boundary hardening：`334cdd4`；實際執行 global／private／loopback／documentation／malformed IPv4 cases，外部工作前 fail closed。
- Targeted／affected verification：public HTTPS 與既有 runtime／staging／rollback／internet gates `33 passed`；三支 shell scripts `bash -n` 通過。
- Full regression：Backend `300 passed, 8 skipped`；Frontend `80 passed`；只有既知 Starlette deprecation warning。
- Negative boundary：HTTP bootstrap 除 ACME challenge 外固定 `404`；production HTTP 只 redirect 到渲染後固定 IP；`22`／`8000`／`8080` 不由 scripts 開放；不含 AWS CLI、DB secret 或 password。
- Sensitivity：bootstrap `404→200` 與 global-IP predicate 反轉皆被 targeted tests 攔截；兩個 mutation 均已還原。
- Rollback：停用 public Nginx／renew timer，原子還原先前 runtime env，重啟並驗證 loopback staging readiness 後才刪除 certificate lineage。
- Artifact：local release `tier0-20260818-334cdd4` 已建立，`co-story.tar.gz` SHA-256 verification 為 `OK`；位於 Git-ignore `outputs/`，尚未上傳。
- Residual risk：尚未在 AL2023 實機驗證 Certbot／Nginx／systemd、未聯絡 Let's Encrypt、未公開 EC2、未做 Browser certificate／cookie 驗證；需明確「核准 Batch 6A」後逐步執行。
