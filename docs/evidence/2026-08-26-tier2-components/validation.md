# Tier 2 story-job local contract 驗證摘要

- Scope／risk／upstream source：R2 queue contract；Tier 2 累積演進方向與共同治理基準 `cae233d`。
- Baseline：Backend `391 passed, 8 skipped`；Frontend `94 passed`。
- Red commit：`179e314`；8 cases 因 domain／application／adapter contract 尚不存在而 assertion fail。
- Green commit：`9f53602`；新增 `StoryJob`、factory、`StoryJobQueue` port 與 memory adapter。
- Targeted verification：story-job domain／queue `8 passed`。
- Affected suite：`backend/tests/test_story*.py` 共 `20 passed`。
- Full Backend regression：`399 passed, 8 skipped`。
- Full Frontend regression：`94 passed`。
- Negative：涵蓋 invalid Room coordinates、同 key 不同內容、competing worker、completion overwrite、unknown／completed reclaim。
- Sensitivity：反轉 enqueue content-conflict guard 後指定 test fail；還原後 targeted 全綠。
- Static／governance：`git diff --check` 與 branch boundary 在 final HEAD 重驗。
- Rollback：可依序 revert Green 與 Red commits；現行 production request flow 未接線。
- Residual risk：memory adapter 無 durability、lease、retry scheduling、multi-process coordination 或 exactly-once 保證。
- Integration deferred：RoomService／API／composition、Data CAS／outbox、durable store／SQS 與 AWS E2E。

## 第二批：lease／failure／retry contract

- Preflight：branch `codex/tier2-components`，共同基準 `cae233d`，開始時 boundary passed、工作樹乾淨。
- Cross-identity：精確案例在舊實作即 `1 passed`；保留為 regression，Green 改為分別解析雙索引並顯式拒絕不同 job。
- Red commits：`c30ca19`（injected clock／lease／token／retry）、`c05f666`（expired complete）與 `181f660`（expired fail）。
- Green commit：`85539ca`；加入 UTC lease、唯一 fencing token、bounded attempts、`fail` 與 `DEAD_LETTERED`。
- Targeted verification：story-job domain／queue `15 passed`。
- Affected suite：`backend/tests/test_story*.py` 共 `27 passed`。
- Full Backend regression：`406 passed, 8 skipped`；Frontend regression：`94 passed`。
- Negative：未到期 competing worker、到期 stale complete／fail、cross-identity、nested payload mutation 與 max-attempt terminal state。
- Sensitivity：將 exact-expiry guard 由 `>=` 改為 `>` 後指定 stale-complete test fail；還原後 targeted 全綠。
- Residual risk：memory timestamp／dead-letter 僅為 contract double；無 durability、SQS visibility mapping、durable DLQ 或 exactly-once。
