# CURRENT：目前工作交接

- 更新日期：2026-08-31
- 目前里程碑：Tier 1、Tier 2、Tier 3均已完整完成。Tier 2 production玩家流程已完成`202 → polling → applied result`；Room進入Round 02／`COLLECTING_ACTIONS`，新AI故事可見，主Queue／DLQ五項均為`0`且DLQ alarm為`OK`／`No actions`。
- 交付策略：已驗證的GitHub OIDC／ECR／Trivy／SSM pipeline作為唯一image交付路徑。Production Web已啟用`async`；後續不得沿用已消耗的玩家E2E核准建立第二回合job或額外呼叫Bedrock。
- Main 整合基準：PR #66／#68已將Support Agent Web／API整合，PR #69修正SSM Document的exact target-driver handoff，PR #70移除CSP阻擋的inline script與Google Fonts；production source exact SHA為`372a2cb77c85530b9cb3bedbd39de9d4b88e535a`，PR #70的Backend／Frontend／branch boundary／container build-scan均全綠。
- Tier 1 完成基準 commit：`07a986a`
- 平行工作狀態：Support Agent API／Web、Tier 2 Web release與CSP corrective均已完成並合併；對應task可維持封存，不需繼續開發。
- Regression：PR #70 strict TDD targeted 6項、Frontend full 112項、Backend CSP gate 9項與Backend full regression均通過；四項GitHub CI全綠。Production activation、rollback與玩家E2E正式證據位於[`Tier 2 Web async activation`](../evidence/2026-08-31-tier2-web-async-activation/validation.md)，CSP修正證據位於[`Support CSP corrective`](../evidence/2026-08-31-support-csp-corrective/validation.md)。
- AWS active release：migration inventory精確`001`–`005`；Web digest為`sha256:f9cc0e650231096cc6a14de1997181601558314195ad6ca31319ad62eb1abdd4`且維持`async`，publisher digest仍為`sha256:23357e315e94842cee8455023b1f87f203fca5b1d11b67b714f4af86efaa2a1b`並為`active`／`running`。兩台Worker均為`sha256:2d5d5866f54879e79882644f4b45af2475650ddc9972e6b91cfe786886cddfbc`、service active、container running、restart `0`、mode `async`、safe diagnostics active。
- 操作邊界：Console-first；使用者操作 AWS Console／SSM。Agent 未經新的 bounded batch 核准不得執行 AWS CLI，且不得執行 S3 讀取或 Bedrock 呼叫。
- Support Agent Phase A：bounded core、PostgreSQL durability、API／session／CSRF／輸入上限／bounded rate limit與Web人工確認UI均已部署production。匿名supported／unsupported規則查詢、Player session草稿、HTTP `200`、無外部submit、service／live／ready與browser rendering均已驗證；inline script與Google Fonts CSP residual亦已由PR #70與run `33398071307`清除。

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
- PR #57只為WorkerRole `bedrock:ApplyGuardrail`補齊既有Guardrail與六個Tokyo APAC profile精確ARN；Change Set `tier2-worker-guardrail-profile-iam-6d814f8-20260830`已`UPDATE_COMPLETE`，實際policy為三個statements、七個精確resources且無wildcard。
- PR #58加入固定allowlist的安全schema診斷，不保存模型原文。Run `33296013600`綁定exact main `81bf54a…`完成ARM64 immutable push、exact-digest Trivy與manifest，兩台Worker再以bounded SSM更新至`sha256:2d5d586…`，均為active／running／restart `0`／async且credential absent。
- 新digest的exactly-one marker `tier2-e2e-20260830-schema-diagnostic-2d5d586-01`只建立一個job、dispatch一次並以attempt `3/3`完成；Bedrock結果`applied`，Room回`COLLECTING_ACTIONS`。Marker已精確清除，Web仍`sync`、publisher active，主Queue／DLQ available與in-flight四項皆為`0`，未自動重跑。
- PR #59–#63完成Web `sync ↔ async` fail-closed contract、candidate preflight、精確restore diagnostics與bounded startup polling。Exact main `bf7de1f…`的production activation與rollback均verified。
- 玩家production E2E使用一個手動世界、三玩家、`maxRounds=4`測試房間。首次單一job／dispatch／invocation以`TRANSIENT_SERVICE_ERROR`終止並立即rollback `sync`；另行核准的人工retry建立一個新job，以`retry_seed=2`限制一次dispatch／一次invocation，結果`applied`。Browser顯示Round 02與新故事，最終Web維持`async`、Publisher／Worker健康、Queue／DLQ空且alarm `OK`。

## Next

1. 將Support Agent Phase A與CSP corrective的production結果保存為Demo素材；不再重跑規則草稿、模型或玩家E2E。
2. 若繼續Support Agent Phase B，先建立獨立RAG／Bedrock／external submit產品與安全邊界；目前production仍只允許static cited rules與`local_draft_only`人工確認草稿。
3. 準備Tier 4前先保存目前monolith、兩台private Worker、SQS／DLQ與單EC2 public edge的baseline；不得直接新增EC2或微服務資源。
4. 成本上限USD 35與2026-09-08清理日不變；既有測試房間不再建立story job。

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
- Nova Lite request、APAC Guardrail profile IAM與safe schema diagnostics均已部署，玩家可見async、一次fail-closed rollback及一次successful bounded retry均已通過；尚未驗證多人長時間連續回合。
- 三次失敗T3B images與兩個成功release images均保留於immutable ECR並受lifecycle limit `10`管理；舊runs不得re-run，ECR storage／scan仍可能產生少量費用。
- Docker actions的 Node.js 20 annotation已以test-first更新至官方 Node.js 24相容版本並通過PR #12、#14、#15 CI；後續仍不得無測試任意升版。
- Story result的PostgreSQL CAS／inbox／completion outbox、async route／composition／Web polling、本機真實PostgreSQL、AWS exactly-one result、production activation／rollback與玩家E2E均已完成。Terminal polling的舊pending feedback與誤導的建立新房間控制已部署；corrective activation已把Web恢復為`async`並通過internal／public live／ready。
- Worker foundation已建立並持續產生單一NAT、public IPv4、兩台Worker與EBS費用；成本上限USD 35、預定清理日2026-09-08。兩台Worker位於同一AZ，只涵蓋instance replacement、不涵蓋AZ failure；HTTPS經NAT的destination尚未以VPC endpoints收斂。
- Migration bridge已證明可讀完整`001`／`002`／`003`／`004`前綴並作為schema activation失敗時唯一rollback target；不得回復不認得newer schema的pre-bridge image，也不得做schema downgrade。
- Support Agent Phase A已通過production smoke與CSP corrective；static retrieval仍無法涵蓋所有自然語言問法，identity digest未加鹽。Bedrock／RAG／外部submit仍不在範圍，不得把`local_draft_only`描述成已送出客服案件。
- iPhone Safari 短期雙向同步已通過，但長時間 polling／visibility 行為仍需在下一次完整多人遊戲觀察。
- 刪房後舊分頁 lifecycle 修正已部署，尚未以 `COMPLETED` 房間做 AWS 多分頁重驗。
- 原始截圖若位於 TemporaryItems／Downloads，不算正式 evidence；入庫前必須去識別化。
