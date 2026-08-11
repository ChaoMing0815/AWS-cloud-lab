# Session lifecycle foundation／activity／authorization 驗證摘要

- Scope／risk：R3 UTC Clock、metadata、activity refresh 與 expiry authorization fail-closed。
- Upstream：Session Feature Spec 與 2026-08-11 五項 observable contract 均已核准。
- Clock Red／Green：`91306ef` → `be8d915`；targeted `6 passed`。
- Metadata Red／Green：`35bc6ba` → `ecf6ec2`；targeted `4 passed`。
- Activity Red／Green：`1960351`、`39cdd70` → `7112f2c`；targeted `14 passed`。
- Authorization Red／Green：`3c13ec3` → `d86173b`；targeted `20 passed`。
- Metadata：Room、Host session、房主 Player session 由同一次 Clock 設為 7 天後。
- Compatibility：demo／legacy payload 缺少 metadata 時保留 `None`，不視為正式有效 session。
- Persistence：PostgreSQL JSON 使用 ISO-8601，還原為 aware UTC datetime。
- Activity：join／action／spark／round／Host mutation 只延長 Room 與正確 actor；replay／失敗／`update_character` 不延長。
- Completion：首次完成固定為完成時間後 7 天，Host session capped；replay 不漂移。
- Authorization：Room／Host／Player 的 `None`、過期與精確 boundary 均拒絕；雙 session 可獨立降級。
- Error order：過期先於 CSRF／version／idempotency replay；GET／polling 不續期。
- Full regression：Backend `105 passed, 7 skipped`。
- Sensitivity：boundary、`None` fail-open、移除 Host／Player expiry guard，以及 refresh placement／actor 錯誤均被抓到並已還原。
- Boundary：before／equal／after、naive datetime、legacy payload、demo room。
- Rollback：回復兩組 Red／Green commits；沒有 SQL migration 或既有資料寫入。
- Residual risk：transfer code／atomic reassign／舊 session revoke 尚未完成。
