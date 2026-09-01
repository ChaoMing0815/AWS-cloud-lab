# CURRENT：目前工作交接

- 更新日期：2026-09-01
- 繳交期限：2026-09-07
- 目前里程碑：ADR-0008 定義的 AWS production 主線已完成，包含可玩 MVP、可觀測／SSM、Web／Story Worker／Data 組件化與自動部署。Tier 4／5 只是 future roadmap，不是當前缺口或 final delivery blocker。
- 狀態判定：以目前已實作、production 狀態與 sanitized evidence 為主。`docs/checkpoints.md` 與 `docs/task-list.md` 是驗收參考與證據整合清單，不得以歷史未勾項否定已有實作與證據的成果。
- 課程對齊：講師已確認 FastAPI＋private PostgreSQL 可作為 Tier 0 Web／DB 分離的等效實作，並已確認 Tier 0–5 的課程能力對映；這不表示最終完成目標仍是 Tier 0–5 全部實作。
- 帳號治理：專案已改用新帳號，舊帳號的 Billing Support 禮貌性點數結果不再適用，不列為 Demo 或繳交阻斷項。已知 MFA、Budget、principal、credits 與基礎資源不重複驗證；只有 change envelope 擴張時才重新核准。

## Production 基準

- Production source exact SHA：`372a2cb77c85530b9cb3bedbd39de9d4b88e535a`。
- Migration inventory：精確 `001`–`005`。
- Web：`sha256:f9cc0e650231096cc6a14de1997181601558314195ad6ca31319ad62eb1abdd4`，runtime `async`，container healthy，restart `0`。
- Publisher：`sha256:23357e315e94842cee8455023b1f87f203fca5b1d11b67b714f4af86efaa2a1b`，service active，container running。
- 兩台 private Worker：`sha256:2d5d5866f54879e79882644f4b45af2475650ddc9972e6b91cfe786886cddfbc`，service active，container running，restart `0`，mode `async`。
- Tier 2 玩家流程已完成 `202 → polling → applied result`；Room 進入 Round 02／`COLLECTING_ACTIONS`，新 AI 故事可見，主 Queue／DLQ 五項皆為 `0`，DLQ alarm 為 `OK`／`No actions`。
- GitHub OIDC／ECR／Trivy／SSM pipeline 是唯一 image 交付路徑；production environment 保留人工核准與 fail-closed health／rollback gate。

## Repo-local release candidate（尚未部署）

- Web UI／Support Widget application code candidate exact SHA：`0b5aaa87cbf68bb4bb0d686f6b65a3c14c48a7f4`，位於整合分支 `codex/final-current-reconciliation`；尚未 merge／push 到 `main`，也尚未觸發 CI/CD 或 production deploy。上方 Production source SHA 與 active digests 仍是唯一 production 基準。
- Candidate 包含玩家可見的 `Release v1.1.0`、新同源 SVG 品牌圖示、終端敘事狀態層級，以及保留當前頁面的像素 Support Widget。Widget 仍只提供 cited／unsupported 規則查詢與 Player-only `local_draft_only` 草稿，不擴張 Bedrock、RAG、MCP 或 external submit。
- 合併後 Frontend regression 為 `124/124`；390×844、768×900、1440×900 browser QA 均確認 Widget toggle 不與 topbar nav 重疊、dialog 不與 composer 相交、無水平溢位，Esc 後 focus 回到 toggle，console 無 error。390 與 768 的 compact dialog 需要內部捲動，屬刻意 responsive 取捨。
- Branch ownership、TDD commits 與整合順序由 `.agents/work-boundaries.json` 與 `docs/governance/parallel-branch-boundaries.md` 記錄；不得重新啟動已完成的 UI／Widget 開發分支。下一個精確起點是整合 review、main 同步與一次新的 bounded `digest-release` deployment batch。

## 已完成範圍

### Tier 0：AWS 可玩 MVP

- Tokyo 上的 public EC2 Web／API、private PostgreSQL RDS、private S3 artifacts、runtime secret 與 bounded Bedrock IAM 均已部署。
- 公開 HTTPS、Nginx、SSM 免 SSH、RDS persistence、三至四玩家完整回合與結局均有 AWS E2E 證據。
- Tier 0 baseline 不使用 NAT、EIP、SSH、ALB、CloudFront、Route 53 或自有網域。Tier 2 Worker foundation 後已新增單一 NAT Gateway 與 public IPv4，不得將 Tier 0 baseline 誤寫為目前全局架構。
- Guardrail 邊界：standalone `ApplyGuardrail` harmful／PII mask 代表性測試已通過；model-integrated Prompt Attack 曾回 `SCHEMA_INVALID`／`503`，未能歸因為 Guardrail intervention。Prompt Injection 仍以 application-layer 明確拒絕作為 defense-in-depth，不宣稱可偵測所有 Prompt Injection。

### Tier 1：CloudWatch、AIOps、SSM

- CloudWatch application／system allowlist logs、7 天 retention、dashboard、alarm、Storyteller token／latency／cost／retry／fallback metrics 均已驗證。
- exactly-one synthetic 500 已完成 `OK → In alarm → OK`；Actions 全程 `No actions`。
- `CoStoryHealthCheck` 已透過 SSM Run Command 驗證 service／live／ready。
- Bounded AIOps 已完成 healthy `NO_ACTION` 與 synthetic incident response；人工拒絕缺乏證據的 `CHECK_DATABASE`，改核准 `RUN_HEALTH_CHECK`。

### Tier 2：Web／Worker／Data

- Public Web／API、SQS／DLQ、兩台 private Story Worker、private PostgreSQL 與 Bedrock 的 async 垂直流程已部署。
- StoryJob identity、idempotency、UTC lease、fencing token、bounded retry、dead-letter、PostgreSQL CAS／inbox／completion outbox 均已實作與驗證。
- Production activation、fail-closed rollback、exactly-one Worker result 與三玩家 production E2E 均已完成。
- 兩台 Worker 位於同一 AZ，目前只驗證 instance replacement，不涵蓋 AZ failure；HTTPS 經 NAT 的 destination 尚未以 VPC endpoints 整合。

### Tier 3：Container 與 CI/CD

- Runtime-only ARM64 image、immutable ECR、exact-digest Trivy HIGH／CRITICAL fail-closed scan、GitHub OIDC 與 bounded SSM release 均已完成。
- Digest release 已實際切換 production container runtime，candidate／public edge／live／ready／Docker health／rollback gates 均有證據。
- 歷史失敗 runs 只作 fail-closed 與矯正證據，不得把「尚未部署」的當時狀態繼續寫成目前狀態，也不得 re-run 舊 workflow。

### 已部署的 bounded Support Agent extension

- Bounded core、static cited rules、unsupported fail-closed、PostgreSQL durability、API／session／CSRF／輸入上限／bounded rate limit 與 Web 人工確認 UI 已部署 production。
- Anonymous supported／unsupported rules lookup、Player `local_draft_only` 草稿、HTTP `200`、service／live／ready、browser rendering 與 CSP corrective 已驗證。
- 此 extension 沒有 Bedrock、RAG、MCP、external submit 或完整 multi-Agent workflow；`local_draft_only` 不得描述為已送出客服案件。這是已完成功能的誠實邊界，不代表本專題尚欠完整 Tier 5。

## 正式證據入口

- Tier 0 public trial：[`docs/evidence/2026-08-19-tier0-public-trial-readiness/validation.md`](../evidence/2026-08-19-tier0-public-trial-readiness/validation.md)
- Tier 0 four-player trial：[`docs/evidence/2026-08-20-tier0-four-player-trial/validation.md`](../evidence/2026-08-20-tier0-four-player-trial/validation.md)
- Tier 1 completion：[`docs/evidence/2026-08-25-tier1-completion/validation.md`](../evidence/2026-08-25-tier1-completion/validation.md)
- Tier 2 Web async activation／rollback／player E2E：[`docs/evidence/2026-08-31-tier2-web-async-activation/validation.md`](../evidence/2026-08-31-tier2-web-async-activation/validation.md)
- Tier 3 production release：[`docs/evidence/2026-08-31-tier3-production-release/validation.md`](../evidence/2026-08-31-tier3-production-release/validation.md)
- Bounded Support Agent production extension：[`docs/evidence/2026-08-31-support-agent-integration/validation.md`](../evidence/2026-08-31-support-agent-integration/validation.md)
- Support CSP corrective：[`docs/evidence/2026-08-31-support-csp-corrective/validation.md`](../evidence/2026-08-31-support-csp-corrective/validation.md)

## Next

1. Review repo-local Web candidate，完成 main 同步與 CI gates；取得使用者對 exact main SHA、active digest、health／rollback gate 的新 bounded deployment approval 後，才觸發一次 `digest-release`，並驗證 production `Release v1.1.0`、品牌圖示、Widget desktop／mobile rendering 與既有 async runtime。
2. 以現有 Tier 0–3 與 bounded Support Agent production 證據建立 5–8 分鐘 final Demo，不重跑 Bedrock、玩家 E2E、synthetic incident 或 rules draft。
3. 整合 final production architecture 與課程能力對映；Tier 4／5 若保留於圖中，必須標示 `Future roadmap / Out of scope for final delivery`。
4. 建立 final evidence index，使 Demo 每一步只連到一個 canonical sanitized evidence。
5. 完成 repository secrets 掃描與 tracked screenshots OCR／人工遮罩 audit。
6. 完成 2026-09-08 清理 runbook，列出現役資源、dependency order、ECR `Retain`、snapshot 決策、owner 與帳單複查方式；未取得人工指示前不執行清理。
7. 最後同步 README、architecture index、project plan、gantt、checkpoints、task list 與 deployment log，移除已被實作取代的歷史未勾項。
8. Tier 4／5、Support Agent Bedrock／RAG／external submit 都是 future scope，不自動開工；若要擴張，必須由使用者另行確認範圍、成本與 AWS change envelope。

## 操作護欄

- Console-first；使用者操作 AWS Console／SSM。Agent 未經新的 bounded batch 核准不得執行 AWS CLI，且不得執行 S3 讀取或 Bedrock 呼叫。
- 保留 EC2 上所有 exactly-one markers，不重跑已完成的模型、incident、synthetic baseline 或第二回合 story job。
- 每次只提供一組同一目的、具停止條件的 Console／SSM 指令。
- 互動式 SSM Session 指令不得使用頂層 `exit`；若需要 exit code，使用 subshell，讓外層 Session 保持開啟。
- Protected file 的唯讀檢查必須使用 `sudo`；gate 失敗只輸出 `stopped` 與診斷摘要，不終止 Session。
- 指令與證據不得輸出 runtime.env、secrets、token、ARN、public IP、Email、account ID 或其他敏感值。
- 成本上限 USD 35，預定資源清理日 2026-09-08。

## Residual risks

- Direct IP certificate 約 160 小時效期，須保留 renewal timer 驗證。EC2 stop／start 若 public IP 改變，URL、certificate 與 allowlist 都需重建。
- EC2 與 RDS 最近一次已知狀態均為運行中。RDS stop 後 storage／backup 仍可能計費，且最長 7 天會自動啟動。
- `CoStoryHealthCheck` 已通過正面 gate，尚未執行 Document 自身的代表性 failure gate。
- 尚未驗證多人長時間連續回合、iPhone Safari 長時間 polling／visibility，以及 `COMPLETED` 房間刪除後的 AWS 多分頁 lifecycle。
- ECR 保留歷史 fail-closed 與 successful release images，lifecycle limit 為 `10`；舊 runs 不得 re-run，storage／scan 仍可能產生少量費用。
- Support Agent static retrieval 無法涵蓋所有自然語言問法，identity digest 未加鹽；Bedrock／RAG／external submit 不在已部署的 bounded scope。
- 原始截圖若位於 TemporaryItems／Downloads 不算正式 evidence；入庫前必須去識別化。
