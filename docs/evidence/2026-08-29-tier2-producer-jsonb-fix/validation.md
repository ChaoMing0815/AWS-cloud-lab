# Tier 2 producer typed JSONB 修正驗證摘要

- Scope／risk／upstream source：production `StoryResolutionProducer`同transaction建立dispatch outbox；R3；來源為已核准exactly-one AWS E2E的rollback-only preflight。
- AWS failure evidence：Room與StoryJob insert通過，但原producer outbox insert在commit前停止；marker rollback為`0`，未送SQS或呼叫Bedrock。
- Production DB boundary：`INSERT=true`、owner吻合、RLS關閉、payload／state constraints已validate、無legacy函式，typed `Jsonb` rollback insert完整通過。
- Baseline：PostgreSQL resolution store與dispatch migration contracts全綠；Backend既有`768 tests collected`。
- Red commit：`036ad4c`；要求dispatch payload以psycopg `Jsonb` adapter傳入精確`schema_version`／`job_id`，舊server-side variadic builder因缺少typed payload而target test失敗。
- Green commit：`cff20ef`；最小修正將完整兩欄message包成`Jsonb`參數，仍維持StoryJob、dispatch outbox與Room save同一transaction順序。
- Targeted verification：resolution store與dispatch migration contracts `12 passed, 1 skipped`。
- Full regression：Backend `768 tests collected`／exit `0`；Frontend `96 passed`。
- Negative／boundary：payload只能包含`schema_version=1`與同一`job_id`；沒有改migration、IAM、SQS schema、retry、Web mode或產品行為。
- Sensitivity：暫時移除`Jsonb` wrapper後target test因收到plain mapping而失敗；mutation已還原並重跑全綠。
- Rollback／residual risk：回復Green commit即可撤銷本機修正；production仍使用舊digest，必須經新exact main、CI／Trivy與獨立`digest-release`核准後，才重啟exactly-one E2E。不得以diagnostic SQL繞過producer。
