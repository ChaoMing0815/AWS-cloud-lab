# Tier 2 PostgreSQL durable story-job contract驗證摘要

- Scope／risk／source：R3 migration與durable queue；治理base `2fbe3c8d4ee941d1dc51a22aab0239cc2a364dae`。
- Baseline：同步前Backend `439 passed, 8 skipped`、Frontend `94 passed`、既有story-job `15 passed`。
- Red commit：`0aea25c`；12 cases因`002`與PostgreSQL adapter不存在而fail，1個明確DSN integration skip。
- Green commit：`d2f406d`；append-only schema與transactional PostgreSQL adapter，targeted `12 passed, 1 skipped`。
- Fixture commit：`6826973`；只把current-schema fixture精確更新為`001＋002`，不改production readiness。
- Boundary coverage commit：`4a401d1`；exact-expiry complete／fail與max-attempt lease dead-letter離線negative。
- Final targeted：PostgreSQL migration／adapter `15 passed, 1 skipped`。
- Story-job affected：`30 passed, 1 skipped`；migration／repository affected：`31 passed, 6 skipped`。
- Full regression：Backend `471 passed, 9 skipped`；Frontend `94 passed`。
- Negative：cross-identity、未到期搶占、stale token、exact expiry、terminal overwrite與invalid state shape均fail closed。
- Atomicity／rollback：每個mutation在connection transaction內；injected write failure原樣逸出並觸發rollback path。
- Sensitivity：將active-token expiry由`>=`改為`>`後complete／fail boundary tests皆fail；還原後targeted全綠。
- Restart：專用`CO_STORY_TEST_DATABASE_URL`存在時驗證新adapter reclaim；本機未提供故1 case明確skip。
- Residual risk：PostgreSQL只提供at-least-once persistence與fencing，不宣稱SQS visibility或distributed exactly-once。
- Deferred：RoomService／API／composition、Data CAS／inbox-outbox、worker process、SQS與AWS E2E仍未接線。
