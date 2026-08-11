# Session lifecycle foundations 驗證摘要

- Scope／risk：R3 UTC Clock、expiry comparator、正式房 metadata 初始化與 JSON round-trip。
- Upstream：Session Feature Spec 與 2026-08-11 五項 observable contract 均已核准。
- Clock Red／Green：`91306ef` → `be8d915`；targeted `6 passed`。
- Metadata Red／Green：`35bc6ba` → `ecf6ec2`；targeted `4 passed`。
- Metadata：Room、Host session、房主 Player session 由同一次 Clock 設為 7 天後。
- Compatibility：demo／legacy payload 缺少 metadata 時保留 `None`，不視為正式有效 session。
- Persistence：PostgreSQL JSON 使用 ISO-8601，還原為 aware UTC datetime。
- Full regression：Backend `71 passed, 7 skipped`。
- Sensitivity：`>=`→`>`、7→8 天、ISO→一般字串均被對應測試抓到並已還原。
- Boundary：before／equal／after、naive datetime、legacy payload、demo room。
- Rollback：回復兩組 Red／Green commits；沒有 SQL migration 或既有資料寫入。
- Residual risk：metadata 尚未接 authorization／activity refresh／API，不可單獨部署。
