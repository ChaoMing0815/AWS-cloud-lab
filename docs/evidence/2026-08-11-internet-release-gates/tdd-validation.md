# Internet release gates 驗證摘要

- Scope／risk／upstream source：R3；production host／origin 邊界、安全 headers 與 live／ready contract。
- Baseline：Backend `144 passed, 8 skipped`。
- Red commit：`e2f32dd test(red): specify internet release gates`。
- Green commit：`36ebf78 feat(green): enforce internet release gates`。
- Targeted verification：`tests/test_internet_release_gates.py`，`9 passed`。
- Full regression：Backend `153 passed, 8 skipped`。
- Negative／boundary：非 allowlist Host 回 400；missing／foreign Origin 的 unsafe API 回 403；readiness failure／exception 回 generic 503。
- Security headers：production HSTS、CSP、nosniff、same-origin referrer；development 不送 HSTS。
- Sensitivity：暫移除 POST Origin gate 後兩個拒絕案例如預期失敗；已還原並重跑 `9 passed`。
- Rollback：回復 Green commit 可撤回 middleware 與 endpoints；沒有外部狀態變更。
- Residual risk：PostgreSQL migration-aware readiness probe 尚未實作；TLS termination／Nginx 仍需 production-parity 驗證。
