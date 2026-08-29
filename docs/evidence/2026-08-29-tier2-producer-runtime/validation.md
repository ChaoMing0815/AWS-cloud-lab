# Tier 2 producer runtime 驗證摘要

- Scope／risk／upstream source：Web compute／AppRole邊界的獨立StoryJob publisher process；R3；ADR-0004與PR #46 dispatch contract。
- Baseline：publisher、production worker、production composition與container contract suite全綠。
- Red commit：`94daf56`；缺少runtime module、production factory與顯式enable gate時共9項目標測試失敗。
- Green commit：`c46f29a`；新增獨立publisher loop與production factory。
- Targeted verification：publisher runtime、dispatch、production worker／composition共69項全綠。
- Full regression：Backend `761 tests collected`，exit code `0`；只有既有Starlette／httpx deprecation warning。
- Negative／boundary：`production`、literal `async`、literal `CO_STORY_PUBLISHER_ENABLED=true`與非空`DATABASE_URL`均在建立AWS client前驗證。
- Sensitivity：暫時將enable gate弱化為truthy後，`TRUE`案例立即失敗且偵測到不應建立的SQS client；mutation已還原並重跑全綠。
- Sanitization：bootstrap exception只輸出固定`publisher_bootstrap_failure`，不輸出DSN、provider detail或secret。
- Rollback／residual risk：刪除或不啟動publisher process即可回復；本批未新增systemd unit、未部署、未套用`005`、未送SQS、Web仍為`sync`。
