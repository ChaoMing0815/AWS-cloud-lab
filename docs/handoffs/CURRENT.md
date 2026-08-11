# CURRENT：目前工作交接

- 更新日期：2026-08-11
- Branch：`codex/session-lifecycle`
- 已驗證功能基準：`30cdffe`（本機 MVP P0 完成）
- Regression：Backend `134 passed, 8 skipped`；Frontend `68 passed`
- AWS：專題 workload 為 0；本批無 AWS 寫入

## Current

- 本機 MVP P0 release gate 已全綠：正式入口、三玩家回合、結局、PostgreSQL restart、LLM recovery、polling 與 session lifecycle。
- Transfer code 為 10 分鐘一次性 hash-only；redeem 原子 rotate Player session／CSRF 並撤銷舊 session。
- 房主轉移自己的 Player 時保留原 Host session；完成房在保留期可唯讀轉移。
- 房主永久刪除有原子 repository contract、204 與三 cookie 清除；刪後所有舊 session／transfer 不可用。
- Browser 已觀察 offline→reconnected、session-expired、completed 與 console 無未處理錯誤。

## Next

```text
講師等價性確認／Tier 0 AWS change envelope
→ 估價、IAM／SG／SSM 邊界與 IaC Red
→ 取得人工核准後才可執行 AWS 寫入
```

無本機 P0 blocker。Residual risk：idempotency 仍是 process memory，不宣稱 multi-process exactly-once。
