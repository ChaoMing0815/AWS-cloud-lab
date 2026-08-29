# CURRENT：目前工作交接

- 更新日期：2026-08-29
- 目前里程碑：Tier 1、Tier 3均已完整完成。Tier 2 schema已至`005`，SQS／DLQ、兩台private Worker及publisher runtime均已在AWS驗證。首次exactly-one鏈路已完成typed JSONB寫入、dispatch、Worker completion與清理，但Bedrock結果為`INVALID_MODEL`；Nova Lite相容性修正已部署至兩台Worker，尚待新的單次live E2E核准，玩家可見async仍未啟用。
- 交付策略：已驗證的GitHub OIDC／ECR／Trivy／SSM pipeline作為唯一自動部署路徑。Production Web仍精確固定`sync`；下一步只可在新核准下建立一個exactly-one test job、單次SQS message與至多一次Bedrock invocation，Web async仍是之後的獨立批次。
- Main 整合基準：PR #56 merge commit `98ded43cad36a59c020f3937db0d360d019749f8`；Nova Lite tool schema相容性Red `f556671`／Green `58680f3`／evidence `d4a3648`及四項CI全綠。PR #55 typed JSONB producer修正已包含於production Web／publisher image。
- Tier 1 完成基準 commit：`07a986a`
- 平行分支治理基準：migration bridge初始註冊Red `4d2decb`／Green `fff9f3f`；Worker第二層guard擴權Red `fcf57d4`／Green `bbfe6dd`。
- Regression：Nova Lite／production Worker／async workflow／publisher／PostgreSQL store相關測試`117 passed, 1 skipped`，完整Backend suite exit `0`，Frontend `96/96`；停用Nova相容轉換的代表性sensitivity會失敗。正式證據位於[`Nova Lite tool schema compatibility`](../evidence/2026-08-29-tier2-nova-tool-schema-compatibility/validation.md)。
- AWS active release：migration inventory精確`001`–`005`；Web與publisher digest均為`sha256:23357e315e94842cee8455023b1f87f203fca5b1d11b67b714f4af86efaa2a1b`，Web為`sync`，publisher為`static`／`active`且container `running`。兩台Worker均為`sha256:94ff5d2c073542393d4e82d1b1c620ee2653730a78a9c655fbf13694024bf8f0`、service active、container running、restart `0`、mode `async`；兩台ECR login credential均已登出清除。
- 操作邊界：Console-first；使用者操作 AWS Console／SSM。Agent 未經新的 bounded batch 核准不得執行 AWS CLI，且不得執行 S3 讀取或 Bedrock 呼叫。
- 平行工作：Support Agent、Tier 2 local／migration、Worker foundation、SQS consumer、Worker artifact pipeline與replacement bootstrap分支均已合併並可封存；Web async未啟用。

## Current

### Tier 0

- 多人 AI 文字 RPG 已部署於 Tokyo：public EC2 Web／API、private PostgreSQL RDS、private S3 artifacts、runtime secret 與 bounded Bedrock IAM。
- 公開 HTTPS、Nginx、SSM 免 SSH、RDS persistence、三至四玩家完整回合與結局均已有 AWS E2E 證據。
- 無 NAT、EIP、SSH、ALB、CloudFront、Route 53 或自有網域。
- Prompt Injection 採 application-layer 明確拒絕作為 defense-in-depth；既有代表性 Guardrail 測試回 `SCHEMA_INVALID`／`503`，不得宣稱 Guardrail Prompt Attack intervention 已通過。

### Tier 1

- `co-story-tier1-observability` 與 `co-story-tier1-operations` 已部署，最後 CloudFormation update 為 `UPDATE_COMPLETE`。
- CloudWatch Agent 收集固定 allowlist application JSONL 與 sanitized system-health JSONL；不收 raw journal、auth、Nginx、query、cookie、prompt 或 secrets。
- Log Groups：`/co-story/tier1/application`、`/co-story/tier1/system`，retention 均為 7 天。
- Dashboard `co-story-tier1-observability` 已驗證 HTTP 5xx／latency、Storyteller latency／tokens／estimated cost／retry／fallback，以及 EC2 memory／root disk。
- Nova Lite 實測：input `206`、output `465`、latency `2,823 ms`、estimated cost `US$0.00012396`。
- `co-story-tier1-application-5xx` 已以 exactly-one synthetic 500 驗證 `OK → In alarm → OK`，Actions 全程 `No actions`。
- IAM policy 只附加 application role；越界 Log Stream 寫入回 `AccessDenied`。最終 Change Set 顯示 managed policy `Modify／Replacement=False`。
- `CoStoryHealthCheck` version 2/default 固定檢查 `/api/v1/live`、`/api/v1/ready`；Run Command 回 `service=active`、`live=200`、`ready=200`。
- Bounded AIOps 已完成 healthy `NO_ACTION` 與 synthetic 500 incident response。人工拒絕缺乏證據的 `CHECK_DATABASE`，改批准 `RUN_HEALTH_CHECK`；沒有 restart、DB secret 讀取或模型重試。
- Storyteller recovery metric pipeline 以 exactly-one zero baseline 驗證 Retries `0`、Fallbacks `0`；此證據不代表真實 retry／fallback incident。
- Tier 1 checkpoints、task list、deployment log 與 sanitized evidence 均已更新。正式證據入口：[`docs/evidence/2026-08-25-tier1-completion/validation.md`](../evidence/2026-08-25-tier1-completion/validation.md)。

### Tier 3 delivery foundation、runtime image、Storyteller 品質與 Tier 2 local contract

- `codex/tier3-delivery` tip `e09327b` 與 `codex/story-quality` tip `ac18cd0` 已經 PR #8 合併 `main`；merge commit 為 `030f11d`。
- Storyteller 現在以 canonical 玩家行動、角色、完整骰點、前景、進度／危機與最近五筆 history 形成因果敘事；round／ending 使用 forced output-only tool 與嚴格 schema，game engine 仍是狀態權威。
- Container 採 runtime-only multi-stage build：digest-pinned Python 3.13 builder 安裝依賴後移除 `pip`／`setuptools`，final 使用 digest-pinned Debian bookworm slim，只保留必要 runtime；`msgpack` 固定為 `1.2.1`。
- PR #8 與合併後 main CI 都在 GitHub runner 完成 Backend／Frontend、container build 與 Trivy HIGH／CRITICAL fail-closed gate；沒有使用 ignorefile、VEX、skip、降低 severity 或 `exit-code: 0`。
- Batch T3A stack `co-story-tier3-delivery` 的 ECR、GitHub OIDC deploy role、AppRole pull policy與 SSM release document 共五項資源均為 `CREATE_COMPLETE`，OIDC trust、IAM 正負控制、ECR immutable／scan／lifecycle 與 SSM document 邊界已通過 Console 驗證。
- PR #14 新增 fail-closed `legacy-bootstrap`／`digest-release`、target-bound driver／unit promotion、mutation rollback與人工限定的 legacy rollback Document；CloudFormation Change Set已套用，stack為 `UPDATE_COMPLETE`。
- PR #15 合併 StoryJob identity、idempotency、UTC lease、fencing token、bounded retry與 dead-letter local contract。Memory adapter只作 contract double，尚未接入 `RoomService`、API、Data、SQS或 production composition。
- Production host已完成 bounded Docker bootstrap：Amazon Linux 2023／aarch64、Docker active、legacy live／ready均為`200`；GitHub `production` environment採required reviewer、main-only且禁止administrator bypass，四項repository variables已設定，未建立長期AWS憑證。
- T3B run `33030554303` 綁定 exact main `0add833c…`：OIDC、ARM64 build與immutable ECR push成功；Trivy v0.70.0在amd64 runner預設選擇`linux/amd64`，無法解析ARM64-only image，故exact-digest scan失敗。`Release exact digest through bounded SSM document`為`skipped`，migration、container啟動與流量切換均未執行；ECR現有一個未通過此workflow scan gate的image，active release仍為Tier 1。正式證據入口：[`docs/evidence/2026-08-27-tier3-production-release/validation.md`](../evidence/2026-08-27-tier3-production-release/validation.md)。
- T3B run `33032162034` 綁定 exact main `d81e4d7…`：canonical ARM64 build／push與Trivy scan成功，SSM送達單一target；migration因container內缺少`/etc/pki/rds/rds-ca.pem`回`migration_failed`。唯讀postflight確認legacy application active、unit／symlink未變、live／ready `200`，沒有release env、transition state、backup、stable assets或container殘留。
- PR #18以strict TDD加入credentials／build前canonical instance target gate、Document首次login／pull前與driver common CA guard、image空mountpoint，以及migration／candidate／stable runtime三處host CA readonly bind；TLS仍為`verify-full`，IAM／OIDC／ECR／rollback權限未變。CloudFormation相對前版只修改`ContainerReleaseDocument.Properties.Content`。
- T3B run `33036267754` 綁定 exact main `2fbe3c8…`：canonical target、OIDC、ARM64 build／immutable push、exact-digest Trivy、RDS CA與migration均通過；candidate因image UID `10001`無法寫入host UID `992`持有的`candidate.jsonl`而回`target_candidate_unhealthy`。唯讀postflight確認legacy application／public edge active、container service inactive、unit／symlink未變、health Document `live=200`／`ready=200`，沒有release env、transition state、backup、stable assets或container殘留。
- PR #20以strict TDD讓image default仍為non-root UID `10001`，但release driver動態驗證host `co-story`非root UID／GID，candidate與stable container使用同一identity；root-only release env固定image／UID／GID三行並拒絕missing、duplicate、root、invalid與identity mismatch。Candidate failure只輸出sanitized state／numeric exit code；CloudFormation template、CloudWatch、IAM、OIDC、ECR、TLS與rollback邊界均未變。
- T3B run `33045168887`綁定exact main `1681736c…`，完整通過OIDC、ARM64 build／immutable push、exact-digest Trivy、SSM migration／candidate／target與public edge gate，首次成功切換container runtime；legacy rollback assets與root-only state均保留。
- PR #21以strict TDD讓Docker HEALTHCHECK從既有runtime allowlist取得Host header，不改loopback probe、TrustedHost policy或release driver。Run `33048585714`綁定exact main `e82c683…`以`digest-release`成功部署；postflight確認四個services active、state `container-active`、Docker `healthy`／failing streak `0`、digest與runtime identity吻合、application log可寫、candidate `0`、live／ready `200`，state／release env精確為`7／3`行。
- Tier 2 PR #19已合併main：append-only `002_create_story_jobs`、PostgreSQL durable queue、UTC lease、fencing、bounded retry與dead-letter local contract完成；production已執行`002`，但尚未建立SQS／AWS Worker或完成AWS E2E。
- Tier 2 read-only integration design gate確認現有Room repository與StoryJob queue各自開transaction，直接串接會形成dual-write gap；完整Room亦含session／CSRF等資料，不得作為job payload。ADR-0004已接受同DB producer transaction與result inbox／completion outbox，第一批只建立未接線application slice，保持現行同步route與玩家行為不變。
- Tier 2 PR #22已合併main：Tx P以單一PostgreSQL transaction完成Room CAS、`RESOLVING`與sanitized immutable StoryJob；Worker每次delivery最多呼叫Storyteller一次；Tx R驗證claim／fencing／lease／Room version並同transaction寫Room、result inbox與completion outbox。Data commit前不ack，commit後ack failure可reclaim並只重送completion；`003`為append-only。現行同步route與production composition仍未接此切片。
- Support Agent PR #23已合併main：Phase A提供allowlisted規則回答與stable citations、unsupported fail-closed、人工確認前問題回報草稿、idempotency、prompt-injection／tool guard與model前敏感資料清理。它只使用靜態knowledge、Mock model與memory repository，尚無API、UI、PostgreSQL、Bedrock、外部提交或AWS部署。
- Tier 2 PR #24已合併main：PostgreSQL production composition的resolve route改為回傳`202`、opaque job ID與canonical `RESOLVING` Room；Web沿用room endpoint polling，60秒只顯示延遲提示，不自動取消、重送或fallback。獨立本機Worker runner以session-free snapshot narrator處理job。程式與`002`／`003` schema已部署，但production固定`sync`，因此玩家流程尚未啟用此切片。
- Tier 2 PR #26已合併main：production Story Worker使用既有Bedrock能力，round與optional ending由單次複合輸出完成；Web process不啟動Worker，local／test維持Mock，缺少必要production設定時在claim與model invocation前fail closed。程式已包含於active image，但Worker服務與AWS queue尚未建立。
- Support persistence PR #25已合併main：append-only`004`、PostgreSQL草稿repository、stable idempotency、divergent replay conflict、人工確認與`local_draft_only`邊界均已整合，production DB已套用`004`。Application／adapter／DB constraint與DB回傳列皆fail closed；沒有API、UI、Bedrock、外部submit或production wiring。真實PostgreSQL adapter／process restart、parallel-write與Tier 2 duplicate-delivery gate均已通過。
- Migration bridge PR #27已合併main：release flow拆成零migration、固定同步流程的`migration-bridge`與獨立`schema-activation`；readiness／runner共用canonical inventory validator，production resolution mode與Worker均精確fail closed，root-only marker綁定verified bridge digest，schema前進後只回復bridge runtime且禁止downgrade。
- Migration bridge階段的CloudFormation `ContainerReleaseDocument`曾更新至version 4/default 4，stack為`UPDATE_COMPLETE`且Change Set只修改Document content。Runs `33139101239`與`33143814648`分別因首次target unit handoff與systemd mode未傳入container而fail closed並完整回復previous digest；PR #29／#30以strict TDD修正，舊runs未重跑。
- Production run `33145778589`綁定exact main `8ab5fe0…`，approval、OIDC、ARM64 build／immutable push、exact-digest Trivy與SSM release均成功。SSM回`container_release=verified mode=migration-bridge`，active digest為`sha256:b9272ee…`、previous digest為`sha256:32bee84…`；沒有執行migration。唯讀postflight確認state／release env／marker為`7／3／2`行、marker綁定active digest、runtime mode `sync`、Docker `healthy`／failing streak `0`、四項services active、candidate `0`、live／ready `200`；此batch完成。
- 首次schema activation因舊stable driver在`preflight-only`誤刪bridge marker而fail closed；migration inventory仍為`001`且服務健康。PR #32修正marker生命週期，PR #33讓SSM Document先只讀驗marker，再由exact target image的同一temporary driver執行preflight與release；Document更新至version 5/default 5，marker依bounded recovery原子恢復。
- Production run `33170836289`綁定exact main `2472e49…`，approval、OIDC、ARM64 build／immutable push、exact-digest Trivy及SSM `schema-activation`全部成功。Active digest更新為`sha256:6d0d732…`，inventory精確為`001`／`002`／`003`／`004`；postflight確認marker清除、state／release env `7／3`行、assets checksum吻合、runtime `sync`、Docker healthy、四項services及live／ready全部通過。
- Tier 2 Worker foundation與replacement-safe runtime已部署：stack `co-story-tier2-worker-foundation`固定20項resource；PR #44修正AL2023 `curl-minimal`衝突後，Launch Template與ASG rolling update均`UPDATE_COMPLETE`，Desired／In service `2／2`。新instance只有在exact image、service active、container running與restart `0`後才送success signal；Web仍為`sync`且未啟用async。
- Tier 2 SQS consumer runtime已完成repo-local strict TDD：exact message schema、單筆20秒long poll、180秒visibility與60秒heartbeat、commit後ack、retry／exception／heartbeat failure不ack；production startup以精確secret ARN在記憶體組成RDS `verify-full` DSN。Worker unit已封裝於同一scanned image並固定non-root、read-only、無published port、awslogs與Worker-only `async`；Web unit仍固定`sync`，尚未部署Worker image或傳送production message。
- Worker artifact pipeline新增獨立manual workflow：只允許main、沿用production approval與bounded OIDC role，build／push ARM64 immutable image、以exact digest執行Trivy HIGH／CRITICAL fail-closed scan並保存manifest；workflow不含SSM或Web release call，不會切換active Web runtime。
- Worker-only run `33233803509`綁定exact main `0ea4b125…`並完整通過production approval、ARM64 build／push、exact-digest Trivy與manifest；digest `sha256:ede0f8e…`經bounded SSM部署至兩台private Worker。SSM `2/2 Success`／response `0`，兩個CloudWatch log streams存在，主Queue／DLQ仍為空；未送message、未呼叫Bedrock，Web仍為`sync`。
- PR #55以typed psycopg `Jsonb`參數修正publisher outbox payload；run `33253308679`綁定exact main `b4b6e28…`完成digest release，Web與publisher均切至`sha256:23357e3…`且Web維持`sync`。首次exactly-one測試只建立一個job，typed JSONB setup、SQS dispatch與Worker completion均成功，但room以`RESOLUTION_FAILED／INVALID_MODEL`結束；marker已清除，主Queue／DLQ available及in-flight四項皆為`0`。
- PR #56只對exact `amazon.nova-lite-v1:0`移除不相容的outgoing tool schema constraints，保留本機strict response validation。Worker image run `33257141550`綁定exact main `98ded43…`完成ARM64 build、exact-digest Trivy及manifest；兩台Worker以bounded SSM更新至`sha256:94ff5d2…`，均為active／running／restart `0`／async，Docker registry credential已登出。升版後尚未建立test job或呼叫Bedrock。

## Next

1. 另行取得新核准後，以Worker digest `sha256:94ff5d2…`建立一個exactly-one AWS test job；只允許單次SQS message與至多一次Bedrock invocation，不自動重跑，Web保持`sync`。
2. 成功時驗證queue→publisher→worker→Bedrock→DB→result並清除marker；失敗時先清理並回報單一根因，不把測試核准延伸為Web async。
3. 上述E2E通過後，才以獨立production envelope將Web從`sync`切換成`async`，完成玩家可見`202`→polling→result E2E及rollback。
4. Tier 2完成後更新completion evidence與架構文件，並依成本上限USD 35於2026-09-08執行既定清理；若需面試展示，只保留可快速重建的最小資產。

## 操作護欄

- 保留 EC2 上所有 exactly-one markers，不重跑已完成的模型、incident 或 synthetic baseline gate。
- 每次只提供一組同一目的、具停止條件的 Console／SSM 指令，不重複檢查已知 MFA、Budget、principal 或基礎資源狀態。
- 互動式 SSM Session 指令不得使用頂層 `exit`；若需要 exit code，使用 subshell，讓外層 Session 保持開啟。
- Protected file 的唯讀檢查必須使用 `sudo`；gate 失敗只輸出 `stopped` 與診斷摘要，不終止 Session。
- 指令不得輸出 runtime.env、secrets、token、ARN、public IP 或其他敏感值。

## Residual risks

- Direct IP certificate 約 160 小時效期；須保留 renewal timer 驗證。EC2 stop/start 若 public IP 改變，URL、certificate 與 allowlist 都需重建。
- EC2 與 RDS 最近一次已知狀態均為運行中。若預估超過 48 小時不使用，依既定清理計畫由使用者手動停止 RDS；storage／backup 仍可能計費，且 RDS 最長 7 天會自動啟動。
- `CoStoryHealthCheck` 已通過正面 gate，尚未執行 Document 自身的代表性 failure gate。
- Nova Lite相容request已通過local／CI並部署至兩台Worker，但尚未以新digest完成live Bedrock invocation；先前唯一一次production invocation以舊Worker結束於`INVALID_MODEL`，不得宣稱AWS E2E已通過。錯誤映射仍較粗，若新測試失敗須保存sanitized原始error分類再診斷。
- 三次失敗T3B images與兩個成功release images均保留於immutable ECR並受lifecycle limit `10`管理；舊runs不得re-run，ECR storage／scan仍可能產生少量費用。
- Docker actions的 Node.js 20 annotation已以test-first更新至官方 Node.js 24相容版本並通過PR #12、#14、#15 CI；後續仍不得無測試任意升版。
- Story result的PostgreSQL CAS／inbox／completion outbox、async route／composition／Web polling與本機真實PostgreSQL process／restart gate均已完成；AWS SQS／DLQ、private Worker foundation、兩台SQS consumer runtime、ASG replacement重建、`005`與publisher runtime均已部署。首次exactly-one已證明dispatch與completion但模型結果失敗；新Worker digest的successful Bedrock result、玩家可見async activation與rollback仍是Tier 2核心缺口。
- Worker foundation已建立並持續產生單一NAT、public IPv4、兩台Worker與EBS費用；成本上限USD 35、預定清理日2026-09-08。兩台Worker位於同一AZ，只涵蓋instance replacement、不涵蓋AZ failure；HTTPS經NAT的destination尚未以VPC endpoints收斂。
- Migration bridge已證明可讀完整`001`／`002`／`003`／`004`前綴並作為schema activation失敗時唯一rollback target；不得回復不認得newer schema的pre-bridge image，也不得做schema downgrade。
- Support Agent static retrieval無法涵蓋所有自然語言問法；identity digest未加鹽，草稿雖已有本機PostgreSQL restart／parallel-write證據，但尚無API層長度／rate limit、API／UI、Bedrock或外部提交。接線前不得宣稱線上客服、RAG或問題提交已完成。
- iPhone Safari 短期雙向同步已通過，但長時間 polling／visibility 行為仍需在下一次完整多人遊戲觀察。
- 刪房後舊分頁 lifecycle 修正已部署，尚未以 `COMPLETED` 房間做 AWS 多分頁重驗。
- 原始截圖若位於 TemporaryItems／Downloads，不算正式 evidence；入庫前必須去識別化。
