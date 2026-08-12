# Non-root runtime bundle 驗證摘要

- 範圍／風險：R3；Tier 0 Nginx、systemd 與 repo 外 runtime environment 契約。
- Baseline：Backend `226 passed, 8 skipped`。
- Red：`9f0ac60 test(red): specify non-root runtime bundle`；三個設定資產不存在而預期失敗。
- Green：`1b888bc feat(green): add non-root runtime bundle`；Nginx 僅轉送 loopback Uvicorn，systemd 以 `co-story` 單 worker 執行，設定由 `/etc/co-story/runtime.env` 載入。
- Targeted：`backend/tests/test_runtime_bundle.py`，3 passed。
- Full regression：Backend `229 passed, 8 skipped`。
- Sensitivity：把 `User=co-story` 改成 `User=root`，non-root assertion 預期失敗；已還原。
- Rollback／residual risk：尚未在 EC2 或 disposable Linux VM 驗證 Nginx／systemd binary syntax、TLS 或 process lifecycle；憑證與 populated environment file 一律留在 repo 外。
