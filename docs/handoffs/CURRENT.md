# CURRENT：目前工作交接

- 更新日期：2026-08-27
- 目前里程碑：Tier 1、Tier 3均已完整完成。第四次T3B首次成功把production從legacy systemd runtime切換至container；其後PR #21修正Docker HEALTHCHECK的production Host header，`digest-release`與唯讀postflight均通過。
- 交付策略：已驗證的GitHub OIDC／ECR／Trivy／SSM pipeline作為後續唯一自動部署路徑。Tier 2 producer／Worker／Data replay-safe local contract、玩家可見async API、production Worker／Bedrock composition與Support Agent Phase A均已整合；先完成不套用新migration的Tier 2 migration bridge，確認newer-schema rollback相容性後，才合併Support persistence並規劃後續AWS部署。
- Main 整合基準：PR #24 merge commit `85990b439a24840778acc8e5c3d48a87528aaebc`；PR #26 merge commit `1d617711d14015fcfaa5a432e1031960ababcf98`，exact-main CI run `33080832206`全綠。
- Tier 1 完成基準 commit：`07a986a`
- 平行分支治理基準：Red `6a76daf`／Green `b772116`。
- Regression：PR #24整合前完整驗證為Backend `558 passed, 11 skipped`、Frontend `96 passed`；merge commit `85990b4…`的main CI `33060850469`之Backend、Frontend、container build／Trivy全綠。真實PostgreSQL story-resolution process/restart integration因未提供專用測試DSN而明確skip，離線transaction／rollback／fault injection均已執行。
- AWS active release：container digest `sha256:32bee84dac17983d867c3f8f8112a34c6380fc4082b1b0a1819312af0d8df106`；legacy release `tier1-20260825-4a51e0e`只作root-only rollback state。
- 操作邊界：Console-first；使用者操作 AWS Console／SSM。Agent 未經新的 bounded batch 核准不得執行 AWS CLI，且不得執行 S3 讀取或 Bedrock 呼叫。
- 平行工作：`codex/tier2-production-worker`已透過PR #26合併並可封存。`codex/support-agent-persistence`的PR #25保持open／`DO NOT MERGE`；新`codex/tier2-migration-bridge`先處理migration readiness與release rollback相容性。兩者均不得部署AWS。

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
- Tier 2 PR #24已合併main：PostgreSQL production composition的resolve route改為回傳`202`、opaque job ID與canonical `RESOLVING` Room；Web沿用room endpoint polling，60秒只顯示延遲提示，不自動取消、重送或fallback。獨立本機Worker runner以session-free snapshot narrator處理job；本機只允許Mock storyteller並在`CO_STORY_ENV=production` fail closed。這批程式尚未部署AWS，production仍使用上述verified container digest，且production尚未執行`002`／`003` migrations。
- Tier 2 PR #26已合併main：production Story Worker使用既有Bedrock能力，round與optional ending由單次複合輸出完成；Web process不啟動Worker，local／test維持Mock，缺少必要production設定時在claim與model invocation前fail closed。這批程式尚未部署AWS，production runtime與資料庫schema均未改變。
- Support persistence PR #25已完成append-only`004`與PostgreSQL草稿repository，但仍保持open／`DO NOT MERGE`。現行migration readiness要求image migration集合與DB完全相等；直接部署`002`／`003`／`004`會讓目前舊image rollback失去readiness，因此整合順序改為先建立migration bridge，再進行schema activation。

## Next

1. `codex/tier2-migration-bridge`先由R3唯讀設計gate定義bridge release、readiness allowlist、rollback與停止條件，再以strict TDD實作；本分支不執行AWS操作或部署。
2. Bridge PR通過review與CI後，才建立綁定exact main SHA的獨立production change envelope；bridge deployment不得套用`002`／`003`／`004`或啟用async Worker。
3. Bridge成為verified active digest且newer-schema rollback contract通過後，才重新審核並合併Support persistence PR #25；不得直接部署目前PR #25。
4. 提供各自隔離的非production測試PostgreSQL DSN，執行process／restart／duplicate-delivery gate；缺少DSN時保留明確skip，不得宣稱durable證據完成。
5. 設計SQS／DLQ、private Worker／Data網段、SG、成本與CloudFormation change envelope，通過action→queue→worker→Bedrock→DB→result E2E及負面連線證據後才提production部署核准。
6. Tier 2 runtime穩定後，另行評估Support Agent API／UI、Nova Lite adapter、rate limiting與observability；外部submit tool仍需獨立核准。
7. 後續任何production更新一律使用新exact main SHA與`digest-release`；previous digest必須取當時verified active state，仍需每次人工核准。
8. Nova Lite round／ending真實品質evaluation仍需另行bounded核准。

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
- Story result的PostgreSQL CAS／inbox／outbox與async route／composition／Web polling已完成本地contract，但真實PostgreSQL process/restart gate仍因缺少專用測試DSN而skip；production Worker／Bedrock adapter、SQS、真正DLQ、lease heartbeat、private Worker與AWS E2E仍是Tier 2核心缺口。
- Migration readiness目前要求DB套用版本集合與image內集合完全相等；一旦`004`成功套用，舊image rollback會因不認得新版本而失敗。Support persistence PR在另行完成相容性策略前不得merge或部署。
- Support Agent static retrieval無法涵蓋所有自然語言問法；identity digest未加鹽、草稿尚無API層長度／rate limit，memory repository不耐restart或多process。接線前不得宣稱線上客服、RAG、Bedrock或問題提交已完成。
- iPhone Safari 短期雙向同步已通過，但長時間 polling／visibility 行為仍需在下一次完整多人遊戲觀察。
- 刪房後舊分頁 lifecycle 修正已部署，尚未以 `COMPLETED` 房間做 AWS 多分頁重驗。
- 原始截圖若位於 TemporaryItems／Downloads，不算正式 evidence；入庫前必須去識別化。
