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

## Production 首次 activation 失敗與 contract 修正

- Production 結果：首次 activation 停在 `web_mode_transition=stopped reason=restore_failed`，沒有建立 test job、SQS message 或 Bedrock invocation。
- Fail-closed 狀態：診斷確認 installed／stable unit 與 runtime 均為 `sync`，service／container／internal／public health 均通過，publisher 仍 active。
- Bounded recovery：人工復原完成後輸出 `web_mode_recovery=verified current=sync state=container-active backups=absent health=passed`；沒有再次 activation。
- Correction Red commit：`6b0c1fc`；代表性測試證明原 contract 缺少 async candidate preflight，且 restore failure 只回報泛化原因。
- Correction Green commit：`568ce51`；在任何 live unit／state mutation 前，以 exact active image、相同 runtime／database env／RDS CA、相同 UID／GID 啟動隔離的 `async` candidate，只檢查 internal live／ready。
- Side-effect boundary：candidate 不建立 job、不發送 SQS message、不呼叫 Bedrock，成功或失敗都清除候選 container；既有同名 container 時 fail closed。
- Restore diagnostics：去敏回報精確區分 unit install、daemon reload、restart、health、state restore 與 cleanup；不輸出 env／secret／玩家內容。
- Verification：`bash -n` 通過；Web transition／container／release rollback contract 共39項通過；`git diff --check` 通過。完整 dependency suite 與 workflow gate 留待 CI，production 再次 activation 需新的明確核准。

## Candidate-preflight 版本的 production 結果與第二次修正

- PR #61 四項CI全綠並合併為exact main `dff1b4d7162daf6002edef6056bbfb5297c491e9`。
- 第二次 activation 在 async candidate 通過後進入live transaction，但回報 `restore_health_failed`並nonzero停止；沒有自動重跑、test job、額外SQS message或Bedrock invocation。
- 唯讀診斷確認installed／stable／backup unit三者byte-identical，Web container已為`sync`、exact image、restart `0`，internal／public live／ready均`200`，candidate absent。
- Bounded recovery只復原已驗證的canonical state並清除兩個forensic backup，輸出 `web_mode_recovery=verified current=sync state=container-active backups=absent health=passed`。
- Publisher的production安裝名稱為`co-story-publisher.service`（repo source asset名稱不同）；正確核對為loaded／active／running／result success／restart `0`／enablement static，container仍為running且exact image。
- Failure-diagnostics Red commit：`9b0733a`；證明restore失敗時會遺失原始target reason，且無法區分service／container／mode／internal／public的live／ready probe。
- Failure-diagnostics Green commit：`4758577`；restore失敗時同時回報原始target phase與精確restore phase，所有reason固定allowlist，不輸出HTTP body、host、env、secret或玩家內容。
- Verification：`bash -n`、21項targeted與41項Web transition／container／release rollback contract及`git diff --check`全數通過；未調高timeout、未改transition mutation／restore語意。完整CI與任何production再試均仍需後續關卡。

## Container startup race 診斷與 bounded polling 修正

- PR #62四項CI全綠並合併為exact main `41128eb5daabf1d7a57d1a88ebd0957283dd6d8a`。
- 第三次 activation 回報原始 `target_container_running_failed` 與 restore `restore_container_running_failed`，證明兩次restart後均在Docker container進入running前即被單次狀態檢查拒絕；candidate已先通過。
- 唯讀診斷後Web已為service active／container running／restart `0`／mode `sync`／exact image，internal／public live／ready均`200`，Publisher仍active／running，candidate absent。
- 再次bounded recovery只復原canonical state並刪除已驗證的兩個forensic backup，不restart、不改unit／image／Publisher，輸出 `web_mode_recovery=verified current=sync state=container-active backups=absent health=passed publisher=active`。
- Startup-polling Red commit：`5ee28ea`；精確證明activation與restore均不會對transient container startup進入retry。
- Startup-polling Green commit：`c602499`；將service／container／restart／image／mode與原有HTTP probes放入同一個30-attempt bounded polling，不新增repeat restart、無限等待、fallback或自動重跑。
- Verification：`bash -n`、23項targeted、43項Web transition／container／release rollback contract與`git diff --check`全數通過；transient target／restore container startup皆有代表性sensitivity，永久不符仍以最後exact phase fail closed。

## Production activation、玩家 E2E 與 rollback 完成

- PR #63四項CI全綠並合併為exact main `bf7de1f4bd8dbb6e3f6791c3160a0532bbe5820f`；production使用同一完整contract，SHA-256為`0f677a5d285fe0a3ee13b2018ca9940e289d2ea24e430afcbdf7222ef30b0fcd`。
- Web activation回`web_async_activation=verified previous=sync current=async`；postflight確認service／container／Publisher active、restart `0`、canonical state `container-active`、backup absent、internal／public health通過。兩台Worker維持active／running／restart `0`／async；空的`0600` Docker config經結構化診斷確認沒有auth、credential helper或credential material。
- 玩家測試只以手動世界建立一個`maxRounds=4`房間、精確三位玩家與第一回合三筆action；setup沒有呼叫世界生成模型。房主第一次只按一次「略過等待者並結算」，Publisher先quiesce，DB精確出現一個pending StoryJob與一個pending dispatch outbox。
- 為確保單一batch最多一次Bedrock invocation，該job在dispatch前固定`retry_seed=2`；第一次dispatch精確`1`、final attempt `3/3`，以`TRANSIENT_SERVICE_ERROR`／`outcome=failed`終止，沒有自動重跑。Web隨即以同一contract回`web_async_rollback=verified previous=async current=sync`；Publisher、Worker、主Queue、DLQ與disabled-actions alarm postflight皆健康／空值。
- 使用者另行核准一次新的人工bounded retry。Web重新activation後，Publisher再次quiesce，房主只按一次「手動重試一次」；DB驗證一個historical failed job與一個新的pending retry job，後者同樣固定`retry_seed=2`。
- Retry結果為`dispatch_attempts=1`、`final_attempt=3`、`invocation_budget=1`、`outcome=applied`，Room進入`COLLECTING_ACTIONS`。Browser顯示Round 02與新的AI故事內容；主Queue available／in-flight／delayed、DLQ available／in-flight均為`0`，DLQ alarm為`OK`／`No actions`。
- 最終production狀態：Web `async`、Publisher active、兩台Worker active／running／restart `0`／async；Web／Publisher digest仍為`sha256:23357e315e94842cee8455023b1f87f203fca5b1d11b67b714f4af86efaa2a1b`，Worker digest仍為`sha256:2d5d5866f54879e79882644f4b45af2475650ddc9972e6b91cfe786886cddfbc`。沒有IAM、CloudFormation、network、schema或固定成本變更。
- Residual UI：Room已正確poll至Round 02／`COLLECTING_ACTIONS`，但上一個「AI 正在整理劇情」operation feedback沒有在polling套用terminal Room後清除；右側canonical AI狀態與故事內容正確。此項列為後續Web UI修正，不否定`202 → polling → applied result`證據。
- 後續repo修正：PR #65（merge `58852b9`）以Red `15dd1b5`／Green `cd7a153`清除該次resolution pending feedback，並移除沒有room-code rotation contract的建立新房間控制；Frontend 98項及四項CI全綠。此註記只代表repo已修正，active production image尚未更新，本production E2E原始結果不變。
- 測試房間保留作正式報告證據，不進行第二回合，最晚於`2026-09-08`清理；成本上限維持USD 35。
