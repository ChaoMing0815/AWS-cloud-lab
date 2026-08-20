# CURRENT：目前工作交接

- 更新日期：2026-08-21
- 近期目標：2026-08-24 第一次報告前完成 Tier 0 AWS 公開試玩收尾、去識別化報告證據、試玩發現的安全／生命週期修正與延遲成本檢查。
- Branch：`codex/tier0-public-trial-ui`，由已同步的 `main` merge commit `3c5db99` 建立；已 push，GitHub PR #4 尚未合併。
- 本機功能 checkpoint：公開試玩 UX／安全失敗記錄 `d2b76ba`；canonical route loading shell `f9d4155`；明確 Prompt Injection 前置拒絕 `6f872b2`；widow／orphan 排版規則 `18fcd21`；首頁公開試玩安全提示 `62b4e02`。
- Regression：Backend `311 passed, 8 skipped`；Frontend `85 passed`（2026-08-19）。
- AWS active release：`tier0-20260819-ee128da`。
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
- Application-layer 明確注入前置拒絕已依嚴格 TDD 完成並部署：Red `a3f12a8`、Green `6f872b2`，active release `tier0-20260819-ee128da`。Batch 9D Browser 驗證英文 override＋system-prompt extraction 在 Storyteller 前回安全 `422`，生成剩餘次數維持 `1`、world fields 不變、`STORYTELLER_FAILURE_LOGS=0`；普通「忽略風雨」故事語句仍通過。此 bounded detector 只是 defense-in-depth，不宣稱能偵測所有 Prompt Injection。
- 同學／友人試玩已限縮為 AWS 外部 E2E 驗證：客觀記錄 HTTPS、三玩家同步、Bedrock 敘事、refresh persistence、錯誤與完成時間；非阻斷性的 UI／UX 回饋不在本輪範圍。操作、停止條件與去識別化證據規則見 `docs/qa/public-trial-guide.md`。
- 尚未部署的本機 UI 收尾已依 TDD 完成：標題與段落使用 responsive `balance`／`pretty` wrapping，列印樣式避免單行跨頁；首頁移除硬編換行並加入「使用暱稱、勿輸入個資／機密」提示。Red commits 為 `a3337b0`、`bf8b193`；Green commits 為 `18fcd21`、`62b4e02`。
- 2026-08-20 完成 Tier 0 四玩家、四回合外部公開試玩：iPhone 12 Safari 房主、macOS Chrome 與兩個 Windows Chrome 玩家均完成加入、角色、四回合、Bedrock 敘事、結局與刪房。AWS E2E 判定為 **PASS with findings**。
- Bedrock CloudWatch 在 22:10–23:00 顯示 Nova Lite `Invocations=6`、input tokens `3,018`、output tokens `1,549`，六次呼叫與世界生成、四回合敘事及結局一致；加權平均 latency 約 `1,940 ms`。EC2 CPU 峰值約 `1.8133%`，RDS `DatabaseConnections` 有非零 client connection。
- Sanitized access log：`200 × 2,671`、`201 × 5`、`204 × 1`、`404 × 317`、`409 × 30`、`5xx × 0`。房間於 22:53:22 成功刪除；317 次 current-room `404` 全部從刪除後 24 秒才開始，確認是舊分頁未停止 polling。
- 公開試玩發現：iPhone Safari 需頻繁手動更新、世界生成前回合數會回預設值、角色儲存後曾顯示原始 JavaScript exception、刪房後各頁未立即導頁，以及回合敘事偏向逐句整合而非深入演繹。前三類 state／error 與刪房 lifecycle 是正式修正候選；敘事品質列為 post-MVP Prompt 優化。
- 8/20 backend metrics／sanitized logs 已入 `docs/evidence/2026-08-20-tier0-four-player-trial/`。六張受測者原圖含 public IP、暱稱、通知或 Browser 資訊，未直接入庫；先以去識別化文字紀錄，報告圖待裁切／遮罩。
- Batch 8A 後 Cost Explorer 的 Total、Bedrock、EC2、RDS 與其他服務當時均顯示 `0`；帳務可能延遲，不能解讀為永久零成本。Credits 尚餘 `US$137.40`，最近到期日 2027-09-08。

## Next

```text
Batch 9B release 與零模型 Browser gate已完成
→ Batch 9C exactly 1 次 synthetic prompt-injection smoke 回 SCHEMA_INVALID／503，未通過
→ Batch 9D 已部署 application-layer 明確注入拒絕，零 Bedrock rejection gate 通過
→ 四玩家四回合外部試玩與 backend evidence 已完成
→ 修正公開 JavaScript exception、刪房導頁／polling lifecycle，並重現 Safari sync／回合選擇問題
→ 製作去識別化報告截圖、完成延遲成本檢查與 PR #4 review／merge
→ 第一次報告後依清理計畫停止或刪除持續計費資源，再進入 Tier 1
```

下一步先以嚴格 TDD 修正公開試玩暴露的原始 JavaScript exception 與刪房後未導頁／持續 polling；Safari sync 與回合選擇回復預設值先做 bounded reproduction。完成 Browser gate、PR #4 review／merge 與延遲成本檢查後，再決定是否建立新的部署 batch。任何後續 S3 讀取、部署或 Bedrock 呼叫都不得沿用舊核准。

## Residual risks

- Prompt Attack 代表性測試明確得到 `SCHEMA_INVALID`／`503`，而非 Guardrail intervention；現有 Guardrail 不可作為唯一防線。
- IAM Access Analyzer basic policy validation 未在 Console 顯示；CloudFormation、R3 tests、安全 review 與正負 Policy Simulator 已通過，但此項仍記為未執行。
- Direct IP certificate 約 160 小時效期；必須保留 renewal timer 驗證。EC2 stop/start 若 public IP 改變，URL、certificate 與 allowlist 都需重建。
- Idempotency store 仍是 process memory，不宣稱 multi-process exactly-once。
- iPhone Safari 未穩定取得即時 canonical state，需要手動重新整理；mobile sync 尚未達 Desktop Chrome 等價。
- 角色儲存後曾把 JavaScript exception 原文顯示給玩家；雖無 backend `5xx` 且遊戲完成，仍需修正 state mapping 與安全錯誤呈現。
- 成功刪房後原 room tabs 未立即導頁並持續 polling，造成大量預期外 `404`；刪除本身已由 `204` 與時序證明成功。
- EC2 與 RDS 持續運行會消耗 credits；artifact objects 依 7 日 lifecycle 到期，但 stack／bucket不會自動刪除。
- 原始截圖位於 macOS TemporaryItems／Downloads 時不算正式 evidence；入庫前須去除 account ID、ARN、IP、instance／subnet／SG ID、endpoint、secret ARN、bucket suffix、通知與不必要的 Browser 資訊。
