# Session Clock primitives 驗證摘要

- Scope／risk：R3 session 技術基礎；只含 UTC Clock 與純 expiry comparator。
- Upstream：Session Feature Spec 已允許 UTC、Clock injection 與 `now >= expires_at` 技術決策。
- Baseline：`62502d5`；Backend `61 passed, 7 skipped`。
- Red：`91306ef`；targeted 6 cases 中 5 個依預期失敗。
- Red reason：缺少 UTC-aware clock、精確到期比較與 naive datetime guard。
- Green：`be8d915`；targeted `6 passed`。
- Full regression：Backend `67 passed, 7 skipped`。
- Sensitivity：暫將 `>=` 改成 `>`，`at-expiry` case 失敗；還原後 `6 passed`。
- Boundary：before／equal／after expiry 與 naive expiry／clock output。
- Rollback：回復 Red／Green commits；沒有 migration 或資料狀態影響。
- Residual risk：尚未接入 Room／repository／authorization／API；五項 observable delta 仍待一次性核可。
