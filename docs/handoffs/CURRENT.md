# CURRENT：目前工作交接

- 更新日期：2026-08-28
- 目前里程碑：Tier 1、Tier 3均已完整完成。Tier 2 migration bridge已透過production pipeline成功部署；尚未套用`002`／`003`／`004`、啟用async Worker或完成AWS三組件E2E。
- 交付策略：已驗證的GitHub OIDC／ECR／Trivy／SSM pipeline作為後續唯一自動部署路徑。Tier 2 producer／Worker／Data replay-safe local contract、玩家可見async API、production Worker／Bedrock composition、Support Agent Phase A與PostgreSQL draft persistence均已整合；migration bridge、唯讀postflight與真實非production PostgreSQL durability gate均已完成。下一步另立`schema-activation` envelope，先只前進schema並保持Web `sync`，再處理AWS Worker／queue與玩家可見async activation。
- Main 整合基準：PR #31 merge commit `89f09bf1802d559a7311dd1004e7c46f62656b03`，exact-main CI run `33163069932`之Backend、Frontend與container build／Trivy全綠；main上的branch-boundary job依workflow設計skipped。
- Tier 1 完成基準 commit：`07a986a`
- 平行分支治理基準：migration bridge初始註冊Red `4d2decb`／Green `fff9f3f`；Worker第二層guard擴權Red `fcf57d4`／Green `bbfe6dd`。
- Regression：PR #25合併後以一次性localhost PostgreSQL 16執行Support draft、StoryJob、Story Result與Web／Worker process durability gate，共`33 passed`、無skip。PR #31再以兩個獨立connection／backend PID、雙barrier與DB端重疊驗證Support draft並行canonical row、divergent idempotency與16-hex collision；targeted `12 passed`、affected `56 passed`、Backend全部72個test files分段全綠、Frontend `96 passed`。Merge commit `89f09bf…`的main CI `33163069932`之Backend、Frontend與container build／Trivy全綠。
- AWS active release：migration bridge container digest `sha256:b9272ee27f1f4f587c2acf7f8672ae15f954c01e919ba311aa6ab83f073e60ff`；previous verified digest `sha256:32bee84dac17983d867c3f8f8112a34c6380fc4082b1b0a1819312af0d8df106`與legacy release `tier1-20260825-4a51e0e`保留作rollback state。Bridge runtime仍為同步模式且未前進schema。
- 操作邊界：Console-first；使用者操作 AWS Console／SSM。Agent 未經新的 bounded batch 核准不得執行 AWS CLI，且不得執行 S3 讀取或 Bedrock 呼叫。
- 平行工作：`codex/tier2-production-worker`、`codex/tier2-migration-bridge`、`codex/support-agent-persistence`與`codex/support-agent-durability`均已合併並可封存；目前沒有進行中的production deployment task。

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
- Tier 2 PR #19已合併main：append-only `002_create_story_jobs`、PostgreSQL durable queue、UTC lease、fencing、bounded retry與dead-letter local contract完成；仍未接`RoomService`、API、production composition、SQS或AWS E2E，且production尚未執行`002`。
- Tier 2 read-only integration design gate確認現有Room repository與StoryJob queue各自開transaction，直接串接會形成dual-write gap；完整Room亦含session／CSRF等資料，不得作為job payload。ADR-0004已接受同DB producer transaction與result inbox／completion outbox，第一批只建立未接線application slice，保持現行同步route與玩家行為不變。
- Tier 2 PR #22已合併main：Tx P以單一PostgreSQL transaction完成Room CAS、`RESOLVING`與sanitized immutable StoryJob；Worker每次delivery最多呼叫Storyteller一次；Tx R驗證claim／fencing／lease／Room version並同transaction寫Room、result inbox與completion outbox。Data commit前不ack，commit後ack failure可reclaim並只重送completion；`003`為append-only。現行同步route與production composition仍未接此切片。
- Support Agent PR #23已合併main：Phase A提供allowlisted規則回答與stable citations、unsupported fail-closed、人工確認前問題回報草稿、idempotency、prompt-injection／tool guard與model前敏感資料清理。它只使用靜態knowledge、Mock model與memory repository，尚無API、UI、PostgreSQL、Bedrock、外部提交或AWS部署。
- Tier 2 PR #24已合併main：PostgreSQL production composition的resolve route改為回傳`202`、opaque job ID與canonical `RESOLVING` Room；Web沿用room endpoint polling，60秒只顯示延遲提示，不自動取消、重送或fallback。獨立本機Worker runner以session-free snapshot narrator處理job；本機只允許Mock storyteller並在`CO_STORY_ENV=production` fail closed。程式已包含於bridge image，但production固定`sync`且尚未執行`002`／`003` migrations，因此玩家流程未啟用此切片。
- Tier 2 PR #26已合併main：production Story Worker使用既有Bedrock能力，round與optional ending由單次複合輸出完成；Web process不啟動Worker，local／test維持Mock，缺少必要production設定時在claim與model invocation前fail closed。程式已包含於bridge image，但Worker未啟動、資料庫schema未改變，也尚未形成AWS Worker／queue部署。
- Support persistence PR #25已合併main：append-only`004`、PostgreSQL草稿repository、stable idempotency、divergent replay conflict、人工確認與`local_draft_only`邊界均已整合。Application／adapter／DB constraint與DB回傳列皆fail closed；沒有API、UI、Bedrock、外部submit或production wiring。合併後真實PostgreSQL adapter／process restart與Tier 2 duplicate-delivery gate已通過；尚無Support draft並行writer測試，production DB亦尚未套用`002`／`003`／`004`。
- Migration bridge PR #27已合併main：release flow拆成零migration、固定同步流程的`migration-bridge`與獨立`schema-activation`；readiness／runner共用canonical inventory validator，production resolution mode與Worker均精確fail closed，root-only marker綁定verified bridge digest，schema前進後只回復bridge runtime且禁止downgrade。
- CloudFormation `ContainerReleaseDocument`已更新至version 4/default 4，stack為`UPDATE_COMPLETE`且Change Set只修改Document content。Runs `33139101239`與`33143814648`分別因首次target unit handoff與systemd mode未傳入container而fail closed並完整回復previous digest；PR #29／#30以strict TDD修正，舊runs未重跑。
- Production run `33145778589`綁定exact main `8ab5fe0…`，approval、OIDC、ARM64 build／immutable push、exact-digest Trivy與SSM release均成功。SSM回`container_release=verified mode=migration-bridge`，active digest為`sha256:b9272ee…`、previous digest為`sha256:32bee84…`；沒有執行migration。唯讀postflight確認state／release env／marker為`7／3／2`行、marker綁定active digest、runtime mode `sync`、Docker `healthy`／failing streak `0`、四項services active、candidate `0`、live／ready `200`；此batch完成。

## Next

1. 另立`schema-activation` change envelope；production套用`002`／`003`／`004`前，必須以read-only preflight確認active bridge digest、digest-bound marker、目前migration inventory `001`、sync runtime與rollback不做downgrade。
2. `schema-activation`只前進append-only schema，candidate與stable Web仍固定`sync`；不得在Worker／queue未完成前切換玩家可見async flow。
3. 設計SQS／DLQ、private Worker／Data網段、SG、成本與CloudFormation change envelope，通過action→queue→worker→Bedrock→DB→result E2E及負面連線證據後才提production部署核准。
4. AWS Worker穩定後，再以獨立repo-local strict-TDD patch與production envelope將Web從`sync`切換成`async`，完成玩家可見`202`→polling→result E2E及rollback。
5. Tier 2 runtime穩定後，另行評估Support Agent API／UI、Nova Lite adapter、rate limiting與observability；外部submit tool仍需獨立核准。
6. Schema activation以外的後續production更新一律使用新exact main SHA與`digest-release`；previous digest必須取當時verified active state，仍需每次人工核准。
7. Nova Lite round／ending真實品質evaluation仍需另行bounded核准。

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
- Forced-tool Storyteller 已通過 fake Converse contract，但尚未以真實 Nova Lite 驗證 round／ending schema 與敘事品質。
- 三次失敗T3B images與兩個成功release images均保留於immutable ECR並受lifecycle limit `10`管理；舊runs不得re-run，ECR storage／scan仍可能產生少量費用。
- Docker actions的 Node.js 20 annotation已以test-first更新至官方 Node.js 24相容版本並通過PR #12、#14、#15 CI；後續仍不得無測試任意升版。
- Story result的PostgreSQL CAS／inbox／outbox、async route／composition／Web polling與本機真實PostgreSQL process／restart gate均已完成；production SQS、真正DLQ、lease heartbeat、private Worker、玩家可見async activation與AWS E2E仍是Tier 2核心缺口。
- Migration bridge已證明可讀完整`001`／`002`／`003`／`004`前綴並作為schema activation失敗時唯一rollback target；不得回復不認得newer schema的pre-bridge image，也不得做schema downgrade。
- Support Agent static retrieval無法涵蓋所有自然語言問法；identity digest未加鹽，草稿雖已有本機PostgreSQL restart／parallel-write證據，但尚無API層長度／rate limit、API／UI、Bedrock或外部提交。接線前不得宣稱線上客服、RAG或問題提交已完成。
- iPhone Safari 短期雙向同步已通過，但長時間 polling／visibility 行為仍需在下一次完整多人遊戲觀察。
- 刪房後舊分頁 lifecycle 修正已部署，尚未以 `COMPLETED` 房間做 AWS 多分頁重驗。
- 原始截圖若位於 TemporaryItems／Downloads，不算正式 evidence；入庫前必須去識別化。
