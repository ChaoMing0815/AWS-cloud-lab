# Tier 2 Web async mode transition contract 驗證摘要

- Scope／risk／upstream：R3；依CURRENT與activation envelope建立Web `sync ↔ async` fail-closed host transaction，不執行AWS變更。
- Baseline：既有container contract與legacy release regression通過。
- Red commit：`92a4cdd`；15個案例因版本化transition script不存在而失敗。
- Green：`ops/release/transition_web_resolution_mode.sh`只接受activate／rollback、exact digest及health host。
- Targeted verification：16項通過；涵蓋activation、rollback、preflight read-only拒絕、post-install checksum drift、target失敗restore、restore failure forensic state與敏感輸出。
- State boundary：七行canonical state、三行release env、installed／stable unit與stable driver的metadata／checksum全部在mutation前核對。
- Mutation boundary：只替換唯一`CO_STORY_RESOLUTION_MODE`來源；image、UID、GID、schema、Publisher、Worker與AWS資源不變。
- Health boundary：service active、container running、restart `0`、exact image／mode、internal及public live／ready皆須通過。
- Rollback：target restart、health或final-state failure會恢復exact previous unit與state；restore失敗保留`0600` forensic state及backup。
- Negative：same-mode、digest mismatch、unit／state drift、existing backup、inactive service及restart count非零均在mutation前停止。
- Sensitivity：暫時停用original-state restore後，target-health rollback測試如預期失敗；還原後16項重新通過。
- Static：`bash -n`通過；本機無`shellcheck`。
- Affected regression：Web transition、container與legacy release共95項通過；需要PyYAML的delivery contract留待CI環境執行。
- Residual risk：尚未push／PR／CI或production執行；queue／job／outbox空值仍由activation batch的Console／SSM preflight另行驗證。
