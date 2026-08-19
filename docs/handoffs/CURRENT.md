# CURRENT：目前工作交接

- 更新日期：2026-08-19
- 近期目標：2026-08-24 第一次報告前完成 Tier 0 AWS 公開試玩、去識別化證據、同學／友人試玩與成本檢查。
- Branch：`codex/tier0-public-trial-ui`，由已同步的 `main` merge commit `3c5db99` 建立；尚未 push／PR。
- 本機功能 checkpoint：公開試玩 UX／安全失敗記錄 `d2b76ba`；canonical route loading shell `f9d4155`。
- Regression：Backend `308 passed, 8 skipped`；Frontend `83 passed`（2026-08-19）。
- AWS active release：`tier0-20260819-2de0424`。
- 操作邊界：Console-first；未經新的 bounded batch 核准不得執行 AWS CLI。使用者操作 AWS Console／SSM，Agent 只提供單一可驗證步驟。

## Current

- Tier 0 AWS 基礎已完成：Tokyo VPC、公網 EC2＋SSM、private PostgreSQL RDS、private S3 artifacts、runtime secret、Guardrail v1 與 bounded Bedrock runtime IAM；無 NAT、EIP、SSH、ALB、CloudFront、Route 53 或自有網域。
- 公開 HTTPS 已啟用：Let's Encrypt short-lived IP certificate、public Nginx 與 renewal timer active；HTTP→HTTPS、bad Host／Origin、security headers、public `8000/8080` 不可達均已驗證。
- Batch 8A 已完成 AWS 三玩家單回合 smoke：三個 Browser sessions 建立角色、同步 action、擲骰、星火決策與房主結算；進入 Round 2，進度 `4（13%）`、危機 `2（7%）`，三端 refresh 後由 private RDS 完整讀回。
- PR #3 已合併至 `main`；merge commit `3c5db99`。Batch 9A 隨後部署 `tier0-20260818-a1160bc`，exact S3 objects `2`、checksum `OK`，application／public Nginx／renew timer active、staging inactive、HTTPS readiness `200`、首頁 `Cache-Control: no-store`。
- Batch 9A 只允許兩次 bounded 世界生成呼叫，均已用完：benign request 回 `200` 並產生完整世界草稿；synthetic prompt-injection request 回 `503`。`503` 只能證明應用失敗，不能證明 Guardrail Prompt Attack filter 介入，故目前不得宣稱 Prompt Attack smoke 通過，也不得在新核准前重試。
- `a1160bc` 已包含 Bedrock `guardContent`／`query` 標記與 installer `umask 0022`，但當時 runtime 沒有安全、正規化的 storyteller failure log；因此無法由既有 log 判定 `503` 是 `CONTENT_REJECTED`、schema invalid 或其他 provider failure。
- Batch 9B 已部署 `tier0-20260819-2de0424`：exact S3 objects `2`、checksum `OK`；application／public Nginx／renew timer active、staging inactive、HTTPS readiness `200`、首頁 `Cache-Control: no-store`。Browser 已驗證 AWS runtime 文案、private PostgreSQL 標示、canonical loading shell、session restore 與近端 validation error；未呼叫 Bedrock。
- 該版本的本機 Red commits 為 `66ee7b5`、`8c9bde0`、`816b817`；Green commits 為 `d2b76ba`、`f9d4155`。世界生成按鈕旁顯示 loading／安全錯誤、關鍵字接受 `、`／`，`／`,`、範例文字泛用化，後端只記 allowlist failure code，不記 prompt、room、player、AWS 原始錯誤或 secret。
- Batch 9C exactly 1 次 synthetic prompt-injection 世界生成已完成：Browser 顯示安全的「世界生成暫時無法完成」、world fields 未變、生成剩餘次數由 `2` 變 `1`；正規化 log 為 `SCHEMA_INVALID`、HTTP `503`。這不是 `CONTENT_REJECTED` 或 Guardrail intervention，證明既有 Prompt Attack filter 對代表性測試不足以單獨依賴；禁止重試。
- Batch 8A 後 Cost Explorer 的 Total、Bedrock、EC2、RDS 與其他服務當時均顯示 `0`；帳務可能延遲，不能解讀為永久零成本。Credits 尚餘 `US$137.40`，最近到期日 2027-09-08。

## Next

```text
Batch 9B release 與零模型 Browser gate已完成
→ Batch 9C exactly 1 次 synthetic prompt-injection smoke 回 SCHEMA_INVALID／503，未通過
→ 以本機嚴格 TDD 加入 bounded application-layer 明確注入拒絕，作為 Guardrail 前置防線
→ 部署後以零 Bedrock 呼叫驗證 client／API rejection、次數不扣除與安全 log
→ 完成同學／友人三玩家試玩、去識別化證據與報告素材
→ 依清理計畫停止或刪除持續計費資源，再進入 Tier 1
```

下一步是純本機 TDD，不需 AWS batch；任何後續 S3 讀取、部署或 Bedrock 呼叫仍必須使用新的明確 bounded batch。

## Residual risks

- Prompt Attack 代表性測試明確得到 `SCHEMA_INVALID`／`503`，而非 Guardrail intervention；現有 Guardrail 不可作為唯一防線。
- IAM Access Analyzer basic policy validation 未在 Console 顯示；CloudFormation、R3 tests、安全 review 與正負 Policy Simulator 已通過，但此項仍記為未執行。
- Direct IP certificate 約 160 小時效期；必須保留 renewal timer 驗證。EC2 stop/start 若 public IP 改變，URL、certificate 與 allowlist 都需重建。
- Idempotency store 仍是 process memory，不宣稱 multi-process exactly-once。
- EC2 與 RDS 持續運行會消耗 credits；artifact objects 依 7 日 lifecycle 到期，但 stack／bucket不會自動刪除。
- 原始截圖位於 macOS TemporaryItems 時不算正式 evidence；入庫前須去除 account ID、ARN、IP、instance／subnet／SG ID、endpoint、secret ARN 與 bucket suffix。
