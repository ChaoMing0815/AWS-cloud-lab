# CURRENT：目前工作交接

- 更新日期：2026-08-19
- 近期目標：2026-08-24 第一次報告前完成 Tier 0 AWS 公開試玩、去識別化證據、同學／友人試玩與成本檢查。
- Branch：`codex/tier0-public-trial-ui`，由已同步的 `main` merge commit `3c5db99` 建立；尚未 push／PR。
- 本機功能 checkpoint：公開試玩 UX／安全失敗記錄 `d2b76ba`；canonical route loading shell `f9d4155`。
- Regression：Backend `308 passed, 8 skipped`；Frontend `83 passed`（2026-08-19）。
- AWS active release：`tier0-20260818-a1160bc`。
- 操作邊界：Console-first；未經新的 bounded batch 核准不得執行 AWS CLI。使用者操作 AWS Console／SSM，Agent 只提供單一可驗證步驟。

## Current

- Tier 0 AWS 基礎已完成：Tokyo VPC、公網 EC2＋SSM、private PostgreSQL RDS、private S3 artifacts、runtime secret、Guardrail v1 與 bounded Bedrock runtime IAM；無 NAT、EIP、SSH、ALB、CloudFront、Route 53 或自有網域。
- 公開 HTTPS 已啟用：Let's Encrypt short-lived IP certificate、public Nginx 與 renewal timer active；HTTP→HTTPS、bad Host／Origin、security headers、public `8000/8080` 不可達均已驗證。
- Batch 8A 已完成 AWS 三玩家單回合 smoke：三個 Browser sessions 建立角色、同步 action、擲骰、星火決策與房主結算；進入 Round 2，進度 `4（13%）`、危機 `2（7%）`，三端 refresh 後由 private RDS 完整讀回。
- PR #3 已合併至 `main`；merge commit `3c5db99`。Batch 9A 隨後部署 `tier0-20260818-a1160bc`，exact S3 objects `2`、checksum `OK`，application／public Nginx／renew timer active、staging inactive、HTTPS readiness `200`、首頁 `Cache-Control: no-store`。
- Batch 9A 只允許兩次 bounded 世界生成呼叫，均已用完：benign request 回 `200` 並產生完整世界草稿；synthetic prompt-injection request 回 `503`。`503` 只能證明應用失敗，不能證明 Guardrail Prompt Attack filter 介入，故目前不得宣稱 Prompt Attack smoke 通過，也不得在新核准前重試。
- `a1160bc` 已包含 Bedrock `guardContent`／`query` 標記與 installer `umask 0022`，但當時 runtime 沒有安全、正規化的 storyteller failure log；因此無法由既有 log 判定 `503` 是 `CONTENT_REJECTED`、schema invalid 或其他 provider failure。
- 本機已依嚴格 TDD 完成下一版：世界生成按鈕旁顯示 loading／成功／安全錯誤、關鍵字接受 `、`／`，`／`,`、範例文字泛用化、AWS／private PostgreSQL 正確標示、canonical deep route 不再短暫閃回 Landing；後端只記 allowlist failure code，不記 prompt、room、player、AWS 原始錯誤或 secret。
- 本機 Red commits：`66ee7b5`、`8c9bde0`、`816b817`；Green commits：`d2b76ba`、`f9d4155`。此版本尚未部署到 AWS，所以目前公開頁面仍不具新的近端錯誤提示與正規化 failure log。
- Batch 8A 後 Cost Explorer 的 Total、Bedrock、EC2、RDS 與其他服務當時均顯示 `0`；帳務可能延遲，不能解讀為永久零成本。Credits 尚餘 `US$137.40`，最近到期日 2027-09-08。

## Next

```text
完成本機文件與 release gate
→ 建立並 checksum 驗證新的 release artifact
→ 提出新的 bounded Batch 9B（exact 2-object S3 read＋安裝；不含模型呼叫）
→ 部署後先以 Browser 驗證 UI、loading shell、HTTPS 與安全 failure log 可用性
→ 另行申請 exactly 1 次 synthetic prompt-injection smoke
→ 只有 log 顯示 CONTENT_REJECTED／等價 Guardrail intervention 且 UI 安全呈現時，才宣稱通過
→ 完成同學／友人三玩家試玩、去識別化證據與報告素材
→ 依清理計畫停止或刪除持續計費資源，再進入 Tier 1
```

下一步只需先建立本機 release；任何 S3 讀取、部署或 Bedrock 呼叫都必須使用新的明確 bounded batch。

## Residual risks

- Prompt Attack 保護目前為「設定已存在、實機結果未歸因」；synthetic request 回 `503`，不是可接受的通過證據。
- AWS active release 尚未包含 `d2b76ba`／`f9d4155`，公開頁面仍可能把世界生成錯誤顯示在視窗外，且 canonical route 會短暫閃回 Landing。
- IAM Access Analyzer basic policy validation 未在 Console 顯示；CloudFormation、R3 tests、安全 review 與正負 Policy Simulator 已通過，但此項仍記為未執行。
- Direct IP certificate 約 160 小時效期；必須保留 renewal timer 驗證。EC2 stop/start 若 public IP 改變，URL、certificate 與 allowlist 都需重建。
- Idempotency store 仍是 process memory，不宣稱 multi-process exactly-once。
- EC2 與 RDS 持續運行會消耗 credits；artifact objects 依 7 日 lifecycle 到期，但 stack／bucket不會自動刪除。
- 原始截圖位於 macOS TemporaryItems 時不算正式 evidence；入庫前須去除 account ID、ARN、IP、instance／subnet／SG ID、endpoint、secret ARN 與 bucket suffix。
