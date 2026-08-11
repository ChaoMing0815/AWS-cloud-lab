# CURRENT：目前工作交接

- 更新日期：2026-08-11
- Branch：`codex/session-lifecycle`
- 已驗證功能基準：`d86173b`（Session expiry authorization fail-closed）
- Regression：Backend `105 passed, 7 skipped`；Frontend `65 passed`（本切片未影響前端）
- 治理：採 [R0–R3 風險式 TDD](../testing-strategy.md)；既有 Approved Spec／ADR／approval log 不重複核可
- AWS：新帳號安全基線已完成；專題 workload 為 0；任何 AWS CLI 需先人工核准 bounded change envelope

## Current

- Session security prerequisites 已完成 Red／Green 與代表性 sensitivity。
- Session Clock／UTC／expiry comparator 與正式房 7 天 metadata 初始化已完成 Red／Green、round-trip 與代表性 sensitivity。
- 核准的 join／Player／Host activity allowlist 已完整接線；replay、失敗與非 allowlist mutation 不延長期限。
- Room／Host／Player expiry 已接入 current reads 與 mutation authorization；`None`／精確到期 fail-closed，雙 session 可獨立降級。
- [Session lifecycle／角色轉移](../features/session-lifecycle-and-transfer.md) 的五項 observable delta 已於 2026-08-11 完成核准。
- 本機 Uvicorn 與臨時 PostgreSQL 已停止；沒有進行中的 AWS change batch。

## Next

```text
Transfer code／atomic reassign／舊 session revoke
→ Browser session-expired／reconnect release gate
```

目前沒有產品核可 blocker。下一次 AWS 工作另建 change envelope，先確認 account、principal、Region、Free plan／credits、Budget、資源集合、權限、費用上限、rollback 與清理責任。

## Pointers

- Session 最近證據：[2026-08-11 validation](../evidence/2026-08-11-session-security-prerequisites/tdd-validation.md)
- Session lifecycle foundations：[2026-08-11 validation](../evidence/2026-08-11-session-clock-primitives/tdd-validation.md)
- AWS 帳號證據：[2026-08-10 baseline](../evidence/2026-08-10-new-account-baseline/validation.md)
- Tier 0 規劃：[AWS deployment plan](../architecture/tier0-aws-deployment-plan.md)
- 8/12–13 P0：[本機 MVP 收斂排程](../daily/2026-08-12-13.md)
