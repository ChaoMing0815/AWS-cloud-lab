# Tier 2 migration bridge 驗證摘要

- Scope／risk／upstream source：R3 repo-local migration bridge；ADR-0006、2026-08-28 Sol 設計 gate。
- Baseline：相關 migration／release／API／Worker／container contract suite 全綠；僅既有 Starlette deprecation warning。
- Red commit：`bcc891b`（inventory、sync composition、Worker second guard、release mode與marker contract）。
- Green commit：`d9d8a57`。
- Targeted verification：migration readiness、production composition、Tier 2 Worker、Tier 3 release workflow／driver contract 全綠。
- Negative／boundary：empty／gap／unknown／duplicate／malformed inventory、sync Worker、bridge marker missing／stale digest與unknown mode均 fail closed。
- Sensitivity：本機暫時破壞 migration call、inventory allowlist、sync flag、marker digest、rollback restore target與workflow bridge case；每次目標測試皆失敗後立即還原。
- Rollback／residual risk：schema activation只回復 verified bridge digest，不做 downgrade；未執行AWS、SSM、workflow dispatch或production deploy。真實 PostgreSQL process/restart gate仍需獨立非production DSN。

## Corrective review（2026-08-28）

- Corrective Red：`e305057`，證明 production mode default／normalization、applied inventory set／未排序查詢與固定 digest release output 都不符合 fail-closed contract。
- Corrective Green：`56b72e7`、`ce53674`。production database composition只接受 literal `sync`／`async`，Worker只接受 literal `async`；注入依賴的既有 security composition 不建立 producer／store，維持既有測試邊界。
- Migration runner：以 `ORDER BY version` 取得 tuple；新資料庫只允許由 audited `001` 起始，非空 applied inventory在任何 migration SQL／version INSERT 前經同一 validator 驗證。
- Release evidence：preflight與verified output均輸出實際 `release_mode`，不含 secret、ARN、instance ID或環境內容。
- Sensitivity：恢復 production default `async`、略過 applied inventory validator、重寫 output 為 `mode=digest-release`，三個目標測試皆失敗後立即還原。
- Final validation：targeted Tier 2／Tier 3 contract、Backend full regression、Frontend `96 passed`、YAML parse、`git diff --check`與branch boundary均通過；PostgreSQL process/restart需專用非production DSN的既有 cases維持 skip。

## Bootstrap compatibility corrective（2026-08-28）

- Scope／risk／upstream source：R3 repo-local corrective；Sol safety gate確認舊production stable driver僅理解`digest-release`，而`migration-bridge`必須由exact scanned target image中的新driver完成。
- Baseline：Tier 3 delivery `16 passed`、legacy bootstrap `56 passed`、GitHub workflow `4 passed`；系統Python缺少`PyYAML`時只出現collection environment error，改用repo `.venv`後baseline全綠。
- Corrective Red：`6fb9631`。rendered SSM Document harness以只接受`digest-release`的fake old driver證明舊routing錯誤，並定義temporary asset、image-ID、preflight／release ordering、TOCTOU與schema stable-driver contract。
- Corrective Green：`8e636fc`。migration bridge pull前改用stable `digest-release preflight-only`；exact target image asset container經image-ID、root-only temporary asset metadata與SHA-256 fences後，使用同一temporary target driver做bridge preflight與release。schema activation仍由upgraded stable driver執行。
- Additional contract evidence：`4a8689d`使替換案例只改content並保留metadata，精確覆蓋second-hash fence；`64a1436`覆蓋target activation失敗時不寫verified marker且恢復previous runtime。
- Targeted／affected verification：new Document harness `10 passed`；Tier 2／Tier 3 affected suites `188 passed`，YAML parse通過。
- Full regression：Backend `620 passed, 11 skipped`；Frontend `96 passed`。
- Sensitivity：old preflight改回`migration-bridge`、target release置於target preflight前、移除regular／symlink gate、移除mode gate、略過asset-container image-ID比較、略過second-hash比較、恢復bridge migration call、提前寫marker、schema activation改用temporary driver；每一項對應目標測試皆失敗後立即還原。
- Rollback／residual risk：temporary assets只防替換／TOCTOU，不能限制已被main-only exact digest／scan／approval授權而以root執行的target driver。pre-mutation failure不改active state或marker；mutation後依driver恢復previous runtime，restore failure保留root-only forensic state。未建立或執行Change Set，未操作AWS／SSM／workflow dispatch／production deploy；PR #25仍為`DO NOT MERGE`。

## First-activation unit handoff corrective（2026-08-28）

- Scope／risk／upstream source：R3 repo-local corrective；production run `33139101239` 的完整rollback evidence與Sol safety gate確認，舊installed／stable unit缺少literal `CO_STORY_RESOLUTION_MODE=sync`，而candidate由target driver明確注入sync，首次target restart才會讀取舊installed unit。舊run與source SHA `cffc85e887f17789396e328d71bbfc42e3630831`均未重跑。
- Baseline：repo `.venv` 的Tier 3 legacy bootstrap與delivery contract全綠；系統Python缺少`PyYAML`僅為collection environment error，未作為Red或產品失敗。
- Corrective Red：`7a5ecb8`（`test(red): define bridge first-activation unit handoff contract`）。不同fixture精確重現舊unit無mode、target unit有literal sync；現行driver第一次restart觀察到舊installed-unit hash，並缺少bridge unit install／reload與source／destination hash failure處理，五項皆為assertion failure。
- Corrective Green：`4701a1c`。只在`migration-bridge`的candidate、previous backups、pending state與target release env後，再驗target unit source SHA-256、原子安裝到installed unit、驗destination SHA-256並`daemon-reload`，再進行第一次target restart。首次health前stable driver／unit維持previous；既有promotion、第二次health、canonical state與最後marker流程不變。
- Additional regression：`86aba88`鎖定`digest-release`與`schema-activation`仍以previous installed／stable unit完成第一次target health，禁止取得bridge-only handoff。
- Targeted／affected verification：Tier 2 readiness／production composition／Worker／async API／rooms API，以及Tier 3 container／workflow／legacy bootstrap／delivery contract為`195 passed`；只有既有Starlette deprecation warning。
- Full regression：Backend `627 passed, 11 skipped`；Frontend `96 passed, 0 skipped`。PostgreSQL process／restart的既有非production DSN缺口維持skip，未以memory double冒充durable證據。
- YAML／syntax／boundary：未修改CloudFormation template；既有Tier 3 YAML parse、`bash -n ops/release/deploy_container.sh`、`git diff --check`與branch boundary均通過。
- Sensitivity：移除bridge-only條件、把unit install移到首次health後、略過`daemon-reload`、略過source／destination SHA、提前stable unit promotion、略過previous installed-unit restore、提前寫marker、恢復bridge migration call；八項各自使對應target test精確失敗後立即還原。
- Rollback／residual risk：handoff或target activation失敗都走既有previous asset／runtime restore；restore失敗維持root-only forensic state。尚未建立／執行CloudFormation Change Set、未操作AWS／SSM／S3／Bedrock／ECR push／workflow dispatch或production deploy；PR #25仍`DO NOT MERGE`。下一個production batch仍需新的人工change envelope、exact scanned image與完整health／rollback postflight。

## Systemd container mode propagation corrective（2026-08-28）

- Scope／root cause：R3 repo-local corrective。production evidence顯示target unit雖有`Environment=CO_STORY_RESOLUTION_MODE=sync`，但systemd Environment只提供Docker CLI process，不會自動傳進container；candidate因本來就明確傳入literal sync而通過，正式target才在production composition的fail-closed guard停止。failed runs `33139101239`、`33143814648`均未重跑。
- Baseline：container contract、Tier 3 legacy bootstrap、production composition與Tier 2 Worker直接相關suite為`112 passed`，僅既有Starlette deprecation warning。
- Corrective Red：`24a2c4d`（`test(red): require systemd container mode propagation`）。unit token contract精確在缺少Docker `--env`相鄰token時assertion failure，不依賴candidate event log。
- Corrective Green：`60bce44`。唯一production修改是在container unit的`ExecStart`加入`--env CO_STORY_RESOLUTION_MODE=${CO_STORY_RESOLUTION_MODE}`；唯一來源仍為精確systemd `sync` Environment，沒有修改`runtime.env`、release env、driver、candidate、migration、schema、CloudFormation或IAM。
- Negative／sensitivity：移除Docker env、把source改為`async`、Docker硬編`sync`與移除candidate literal sync，均使各自target contract failure後立即還原；permanent unit negatives亦拒絕empty、uppercase、前後空白、runtime-env-only與非canonical source。
- Final validation：Tier 2／Tier 3 affected contract為`204 passed`；Backend full regression為`636 passed, 11 skipped`（既有非production PostgreSQL process／restart cases），Frontend為`96 passed, 0 skipped`。YAML parse、`bash -n ops/release/deploy_container.sh`、`git diff --check`與branch boundary均通過。
- 未建立／執行Change Set，未操作AWS／SSM／S3／Bedrock／ECR push／workflow dispatch或production deploy；PR #25仍`DO NOT MERGE`。

## Production migration bridge（2026-08-28）

- CloudFormation stack `co-story-tier3-delivery`為`UPDATE_COMPLETE`；`ContainerReleaseDocument` version 4/default 4。已核准Change Set只修改`AWS::SSM::Document`的`Content`，沒有IAM、OIDC、ECR、AppRole attachment或其他資源變更。
- Runs `33139101239`與`33143814648`分別在首次target activation暴露installed unit handoff與systemd環境未傳入container的問題；兩次皆回`target_activation_failed`並回復verified previous digest、healthy container與公開`live=200`／`ready=200`，未寫bridge marker。舊run與舊SHA均未重跑。
- PR #29／#30以strict TDD完成bridge-only unit handoff及Docker `--env CO_STORY_RESOLUTION_MODE=${CO_STORY_RESOLUTION_MODE}`；exact main `8ab5fe0239cf24e6420a6d983a4cb50078b4e7fc`的CI run `33145389354`全綠。
- 使用者明確核准exact main `8ab5fe0…`與previous digest `sha256:32bee84…`的`migration-bridge`；production run `33145778589`之approval、OIDC、ARM64 build／immutable push、exact-digest Trivy與bounded SSM release均成功。
- SSM回`Status=Success`、`ResponseCode=0`，並輸出`container_release=verified mode=migration-bridge image_digest=sha256:b9272ee27f1f4f587c2acf7f8672ae15f954c01e919ba311aa6ab83f073e60ff previous_image_digest=sha256:32bee84dac17983d867c3f8f8112a34c6380fc4082b1b0a1819312af0d8df106`。
- 此mode沒有執行`002`／`003`／`004` migration，也沒有啟用async Worker。GitHub artifact `tier3-delivery-metrics-33145778589`保留sanitized delivery timing。
- 唯讀host postflight：application、public edge、CloudWatch Agent與system-health timer均為`active`；transition／release env／bridge marker均為`root:root:600`且精確`7／3／2`行；state為`container-active`、marker為`verified-bridge`且digest與active release一致；installed unit只含一份literal `sync`來源與一份顯式container env傳遞。
- Runtime postflight：container running、Docker health `healthy`／failing streak `0`、container內resolution mode `sync`、candidate count `0`、legacy rollback unit preserved、公開live／ready均為`200`。首次檢查因shell在`sudo wc`前開啟root-only檔案且Docker查詢漏用`sudo`而產生空值；補充唯讀gate修正檢查方式後全數通過，該空值不代表runtime失敗。
- 費用增量限於immutable ECR image storage／scan與GitHub Actions時間；既有ECR lifecycle limit `10`維持。Previous image未留在host cache不是失敗條件，rollback driver可由immutable ECR拉取exact previous digest `sha256:32bee84…`；不得以schema downgrade回復。
