# CURRENT：目前工作交接

- 更新日期：2026-08-26
- 目前里程碑：Tier 1 已完整完成；先平行建立 Tier 3 delivery foundation 與改善 Storyteller／遊玩品質，再回到 Tier 2 Web／Story Worker／Data 切割。
- 交付策略：`codex/story-quality` 與 `codex/tier3-delivery` 使用獨立 worktree 與路徑白名單；完成整合、完整 regression 與自動部署示範後，再以既有 pipeline 推進 Tier 2。
- Branch：`codex/tier1-runtime-observability`
- Tier 1 完成基準 commit：`07a986a`
- 平行分支治理基準：Red `6a76daf`／Green `b772116`。
- Regression：Backend `363 passed, 8 skipped`、Frontend `94 passed`。
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

## Next

兩個平行 task 都從包含治理基準的同一 commit 建立：

1. `codex/story-quality`：以嚴格 TDD 定義敘事 contract，讓玩家行為、角色、骰點、進度、危機與結局產生可驗證的因果劇情；不得修改 delivery／AWS 路徑。
2. `codex/tier3-delivery`：以嚴格 TDD 建立 current monolith 的 Docker、ECR、GitHub OIDC、CI/CD、SSM release、health gate 與 rollback；不得修改產品行為。
3. 兩分支交付前執行 `scripts/check_branch_boundaries.py`，越界即停止並交回整合 task。
4. 整合 task依序整合 delivery foundation 與 story quality，重跑 Backend／Frontend／container regression。
5. Repo-local gate 全綠後，另提出含成本、安全、IAM、驗證與 rollback 的 Tier 3 AWS bounded batch，供使用者核准。
6. 自動部署垂直切片完成後，再以相同 pipeline 推進 Tier 2 queue／job／idempotency 與三組件 AWS E2E。

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
- Idempotency store 目前仍為 process memory，不宣稱 multi-process exactly-once；這是 Tier 2 的核心設計缺口。
- iPhone Safari 短期雙向同步已通過，但長時間 polling／visibility 行為仍需在下一次完整多人遊戲觀察。
- 刪房後舊分頁 lifecycle 修正已部署，尚未以 `COMPLETED` 房間做 AWS 多分頁重驗。
- 原始截圖若位於 TemporaryItems／Downloads，不算正式 evidence；入庫前必須去識別化。
