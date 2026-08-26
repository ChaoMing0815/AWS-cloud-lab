# CURRENT：目前工作交接

- 更新日期：2026-08-26
- 目前里程碑：Tier 1 已完整完成；Tier 3 delivery foundation、Storyteller 品質與 runtime-only container 已經 PR #8 合併 `main`，Batch T3A control plane 已建立並通過細部安全驗證，但尚未部署容器。
- 交付策略：先完成 Tier 3 自動部署垂直切片，再以同一 pipeline 推進 Tier 2。PR／`main` CI 與 production release 分離；下一次 image push、ECR scan、SSM release 與 rollback 驗證必須另建 T3B bounded change。
- Main 整合基準：PR #8 merge commit `030f11d`。
- Tier 1 完成基準 commit：`07a986a`
- 平行分支治理基準：Red `6a76daf`／Green `b772116`。
- Regression：Backend `388 passed, 8 skipped`、Frontend `94 passed`；runtime-only image 的 Tier 3 affected suite `13 passed`。PR #8 四項 checks 全綠；merge commit `030f11d` 的 main CI run `32939458577` 亦通過 Backend、Frontend 與 container build／Trivy。Trivy v0.70.0 結果為 `HIGH=0`、`CRITICAL=0`。
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

### Tier 3 delivery foundation、runtime image 與 Storyteller 品質

- `codex/tier3-delivery` tip `e09327b` 與 `codex/story-quality` tip `ac18cd0` 已經 PR #8 合併 `main`；merge commit 為 `030f11d`。
- Storyteller 現在以 canonical 玩家行動、角色、完整骰點、前景、進度／危機與最近五筆 history 形成因果敘事；round／ending 使用 forced output-only tool 與嚴格 schema，game engine 仍是狀態權威。
- Container 採 runtime-only multi-stage build：digest-pinned Python 3.13 builder 安裝依賴後移除 `pip`／`setuptools`，final 使用 digest-pinned Debian bookworm slim，只保留必要 runtime；`msgpack` 固定為 `1.2.1`。
- PR #8 與合併後 main CI 都在 GitHub runner 完成 Backend／Frontend、container build 與 Trivy HIGH／CRITICAL fail-closed gate；沒有使用 ignorefile、VEX、skip、降低 severity 或 `exit-code: 0`。
- Batch T3A stack `co-story-tier3-delivery` 的 ECR、GitHub OIDC deploy role、AppRole pull policy與 SSM release document 共五項資源均為 `CREATE_COMPLETE`，OIDC trust、IAM 正負控制、ECR immutable／scan／lifecycle 與 SSM document 邊界已通過 Console 驗證。
- ECR 仍為空；尚未 push／scan image、設定或執行 GitHub production release、執行 SSM command、bootstrap Docker 或變更 AWS active release。正式證據入口：[`docs/evidence/2026-08-26-tier3-control-plane/validation.md`](../evidence/2026-08-26-tier3-control-plane/validation.md)。

## Next

1. 建立 Tier 3 production release 的 T3B change envelope，列出 GitHub environment／variables、previous digest、image push／ECR scan、Docker bootstrap、SSM readiness、rollback、成本與停止條件；目前尚未授權執行。
2. T3B 核准後由使用者啟動 `workflow_dispatch` 並通過 GitHub `production` environment gate；不得用 push `main` 取代人工批准。
3. 以 exact image digest 驗證 ECR scan、EC2 candidate `live`／`ready`、public edge、active release 與 previous digest rollback；成功與失敗都保存去識別化 timing evidence。
4. 另行準備最小 Nova Lite bounded evaluation：round 與 ending 各一次；不得由 Agent 呼叫，且必須另行核准。
5. 自動部署垂直切片完成後，再以相同 pipeline 推進 Tier 2 queue／job／idempotency 與三組件 AWS E2E。

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
- Tier 3 repo-local／PR image 已通過 Trivy，但 ECR 仍為空，尚未取得 ECR scan 或 application release 證據；不得把 T3A 約 55 分鐘人工安全審查或 PR CI 時間當成應用程式部署時間。
- Idempotency store 目前仍為 process memory，不宣稱 multi-process exactly-once；這是 Tier 2 的核心設計缺口。
- iPhone Safari 短期雙向同步已通過，但長時間 polling／visibility 行為仍需在下一次完整多人遊戲觀察。
- 刪房後舊分頁 lifecycle 修正已部署，尚未以 `COMPLETED` 房間做 AWS 多分頁重驗。
- 原始截圖若位於 TemporaryItems／Downloads，不算正式 evidence；入庫前必須去識別化。
