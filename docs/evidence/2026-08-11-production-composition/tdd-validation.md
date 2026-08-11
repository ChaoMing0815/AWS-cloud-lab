# Production fail-closed composition 驗證摘要

- Scope／risk／upstream source：R3；依 SSOT、AWS deployment plan 與 session 7 天期限，限制 production 組態、Demo seed 與 cookie。
- Baseline：Backend `134 passed, 8 skipped`；Frontend `71 passed`。
- Red commit：`9373bc9 test(red): specify production fail-closed composition`。
- Green commit：`996bc75 feat(green): fail closed in production composition`。
- Targeted verification：`tests/test_production_composition.py`，`9 passed`。
- Full regression：Backend `144 passed, 8 skipped`。
- Negative／boundary：缺少 DB、Secure cookie、allowed hosts／origins、storyteller，或 DB TLS 非 `verify-full`／缺 CA 時拒絕啟動。
- Data boundary：production 不建立 `BONUS7`；development 預設行為維持。
- Sensitivity：暫改 local-room cookie 為 1 天後目標測試如預期失敗；已還原並重跑 `9 passed`。
- Rollback：回復 Green commit 即恢復舊 composition；未執行 migration 或 AWS 操作。
- Residual risk：allowed hosts／origins 尚未接上 request middleware；Bedrock production adapter、`/live`／`/ready` 仍是下一批 release gate。
