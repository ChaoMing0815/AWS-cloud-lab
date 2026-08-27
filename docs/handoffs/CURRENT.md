# CURRENT：目前工作交接

- 更新日期：2026-08-27
- 目前里程碑：Tier 1 已完整完成；Tier 3兩次T3B均安全fail closed。第一次在Trivy平台解析停止；第二次ARM64 exact-digest scan通過並送達SSM，但migration因container未掛載host RDS CA而在任何mutation前停止。PR #18已合併target canonical validation與CA preflight／readonly mount修正，production仍維持Tier 1。
- 交付策略：先以PR #18合併後template建立只更新`ContainerReleaseDocument`新版本的Change Set，修正GitHub canonical instance variable，再以新的exact `main` SHA重新核准T3B；Tier 2可平行完成PostgreSQL durable contract PR，但在首次container transition成功前不合併。
- Main 整合基準：PR #18 merge commit `114b8a838276751019d49b416339220fd3a274ab`。
- Tier 1 完成基準 commit：`07a986a`
- 平行分支治理基準：Red `6a76daf`／Green `b772116`。
- Regression：PR #18 Backend全數通過、`8 skipped`，Frontend `94 passed`，Tier 3 affected `63 passed`；PR CI的branch boundary與container build／Trivy全綠。Tier 2目前新PostgreSQL targeted `12 passed, 1 skipped`，但仍停在migration readiness治理擴權前，尚未完成Green／完整regression。
- AWS active release：`tier1-20260825-4a51e0e`
- 操作邊界：Console-first；使用者操作 AWS Console／SSM。Agent 未經新的 bounded batch 核准不得執行 AWS CLI，且不得執行 S3 讀取或 Bedrock 呼叫。

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

## Next

1. PR #18 merge後main CI `33034586914`已全綠；以本次context／governance commit形成的最終exact main template建立bounded Change Set，只接受`ContainerReleaseDocument` Modify／NewVersion，其餘任何resource／IAM／replacement變更立即停止。
2. Change Set完成後，使用者把GitHub repository variable `TIER3_INSTANCE_ID`重新貼為單行canonical ID；不得含Tab、空白或換行。以新exact main重新形成並核准T3B，舊runs `33030554303`／`33032162034`均不得re-run。
3. 新run成功後另批唯讀驗證container service、public edge、active digest、legacy rollback state與delivery metrics，再判定Tier 3 gate。
4. `codex/tier2-components`在新治理基準下只更新migration readiness current-schema fixture，完成PostgreSQL durable queue strict TDD、完整regression、boundary與PR；PR保持未合併直到Tier 3首次transition完成。
5. Tier 3完成後再決定Tier 2 production接線、SQS與三組件AWS E2E；Nova Lite round／ending evaluation仍需另行bounded核准。

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
- 兩次失敗T3B已在ECR留下immutable ARM64 images；第一個未通過workflow Trivy，第二個通過scan但migration前fail closed。兩者都不是production release且不得re-run；ECR storage／scan仍可能產生少量費用。
- Docker actions的 Node.js 20 annotation已以test-first更新至官方 Node.js 24相容版本並通過PR #12、#14、#15 CI；後續仍不得無測試任意升版。
- StoryJob memory adapter與既有 idempotency store都不宣稱 durable lease或multi-process exactly-once；Data CAS／outbox、SQS、真正DLQ與restart recovery仍是Tier 2核心缺口。
- iPhone Safari 短期雙向同步已通過，但長時間 polling／visibility 行為仍需在下一次完整多人遊戲觀察。
- 刪房後舊分頁 lifecycle 修正已部署，尚未以 `COMPLETED` 房間做 AWS 多分頁重驗。
- 原始截圖若位於 TemporaryItems／Downloads，不算正式 evidence；入庫前必須去識別化。
