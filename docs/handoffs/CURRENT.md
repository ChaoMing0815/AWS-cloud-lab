# CURRENT：目前工作交接

- 更新日期：2026-09-05
- 繳交期限：2026-09-07
- 目前里程碑：ADR-0008 定義的 AWS production 主線已完成，包含可玩 MVP、可觀測／SSM、Web／Story Worker／Data 組件化與自動部署。Tier 4／5 只是 future roadmap，不是當前缺口或 final delivery blocker。
- 狀態判定：以目前已實作、production 狀態與 sanitized evidence 為主。`docs/checkpoints.md` 與 `docs/task-list.md` 是驗收參考與證據整合清單，不得以歷史未勾項否定已有實作與證據的成果。
- 課程對齊：講師已確認 FastAPI＋private PostgreSQL 可作為 Tier 0 Web／DB 分離的等效實作，並已確認 Tier 0–5 的課程能力對映；這不表示最終完成目標仍是 Tier 0–5 全部實作。
- 帳號治理：專案已改用新帳號，舊帳號的 Billing Support 禮貌性點數結果不再適用，不列為 Demo 或繳交阻斷項。已知 MFA、Budget、principal、credits 與基礎資源不重複驗證；只有 change envelope 擴張時才重新核准。

## Production 基準

- Latest application-bearing `main` SHA：`c5f3d038f363a29c8ac1b402d501f0a1ed6bad19`；此 SHA 已包含尚未部署的 Web `Release v1.1.3`與已部署的corrective Worker hotfix。後續docs-only merge可能繼續推進repository tip；新task必須以`git rev-parse origin/main`查詢即時tip，不得把docs-only SHA、repo tip或application-bearing SHA誤認為目前Web production source。
- Active Web source exact SHA：`09dc09af12b3903f34aefe910699a066a3b56798`；玩家目前看到 `Release v1.1.2`。待展示的 Web `Release v1.1.3` 尚未觸發 production release。
- Active Worker source exact SHA：`c5f3d038f363a29c8ac1b402d501f0a1ed6bad19`；2026-09-05 corrective ToolUse hotfix 已只部署至兩台 private Worker。
- Migration inventory：精確 `001`–`005`。
- Web：`sha256:c3e6c215c26043678962528d65f73f39761b141170455e279cc89cc1f6b6b27c`，runtime `async`；run `33844595314` 由 exact source `09dc09a…` 完成 `Release v1.1.2` deployment。Web、首頁版號與 Publisher 均未被本次 Worker hotfix 修改。
- Publisher：`sha256:23357e315e94842cee8455023b1f87f203fca5b1d11b67b714f4af86efaa2a1b`，service active，container running。
- 兩台 private Worker：`sha256:439059c4a3f94657c2a9403732237ec3e576041cd962c7e789b89b1ec7d9fd73`，`CO_STORY_BEDROCK_MAX_TOKENS=3000`，service enabled／active、container running、restart `0`、mode `async`、ECR registry與暫存credential absent。立即rollback為 digest `sha256:1655de7a07b93b08564693d2bfc678ba2d1f616dda01cf74a8efbd920cf084f4` 加 token budget `3000`。
- Tier 2 玩家流程已完成 `202 → polling → applied result`；corrective production驗證於原Round 02失敗畫面手動重試，沿用鎖定行動／骰點／星火並成功產生AI故事、進入Round 03；規則結果只套用一次。
- GitHub OIDC／ECR／Trivy／SSM pipeline 是唯一 image 交付路徑；production environment 保留人工核准與 fail-closed health／rollback gate。

## 2026-09-01 UI／Support Widget production release

- UI terminal refresh 與像素 Support Widget 已合併、push 至 `main` 並部署 production，不再是 repo-local candidate；不得重新啟動或延續已完成的 `codex/ui-terminal-refresh`、`codex/support-pixel-widget` 分支。
- 玩家可見 `Release v1.1.0`、新同源 SVG 品牌圖示、終端敘事狀態層級與保留當前頁面的像素 Support Widget 均已上線。Widget 仍只提供 cited／unsupported 規則查詢與 Player-only `local_draft_only` 草稿，不擴張 Bedrock、RAG、MCP 或 external submit。
- Exact main CI run `33493821544` 全綠；release run `33494151458` 綁定 exact SHA `1297a6acabaf30ca4ec2205e7641b7ab83cef781`，以 previous digest `sha256:f9cc0e6…` 完成 `digest-release`，新 active Web digest 為 `sha256:5a10597…`。Publisher 與兩台 Worker digest未變。
- 整合 Frontend regression `124/124`；production Browser QA確認 `Release v1.1.0`、品牌圖示、Widget、Esc focus return，390×844 下 toggle／nav與dialog／composer均不重疊、無水平溢位、console無error／warning。390與768的compact dialog內部捲動是刻意responsive取捨。
- Release後發現既有Direct IP憑證已過期；根因不是本次Web image，而是`/var/lib/co-story`為`root:co-story 0750`，Nginx worker無法穿越，造成ACME token雖存在仍回`404`。Production已加入精確ACL `user:nginx:--x`、同一renewal unit成功換發並reload；外部strict TLS首頁／live／ready均回`200`。下一次timer自動執行尚未觀察，repo防回歸仍是明確未完成項。

## 2026-09-02 寵物規則助手 production release

- 兩日版寵物規則助手與擴充的 deterministic rules retrieval 已透過 PR #71 合併；PR #72 完成文件口徑收斂，production source exact SHA 為 `4db923f4d24aae0aca25c3fbe525f765f9d5023b`。
- Main CI run `33577941894` 第一次只因 Docker Hub 拉取 BuildKit timeout、在 build／scan 前停止；failed jobs rerun 的 attempt 2 全綠。Release run `33578331749` 通過 production approval、OIDC、ARM64 build／immutable push、digest fence、Trivy、bounded SSM 與 delivery metrics。
- Active Web 已更新為 `sha256:14d8e0f…` 並維持 `async`；前一個 `sha256:5a10597…` 保留為 rollback。Publisher、兩台 private Worker 與 migration inventory `001`–`005` 未變。
- Production Browser QA 已驗證 390／768／1440 viewport、中文片語不拆分、寵物動畫／dialog、六個規則主題、supported citation、unsupported不猜測、`/support`玩家頁退場、無水平溢位及 console error／warning；strict TLS首頁／live／ready皆為`200`。
- 這仍是 cited deterministic rules assistant，不是 RAG；沒有 LLM、embedding、vector store、Bedrock、MCP、external submit、第二個 story job 或新的 rules draft。

## 2026-09-02 寵物視覺 v1.1.1 production release

- PR #74 已將 `codex/pet-visual-refresh-v1-1-1` 合併至 exact main `4fb06d0fa33c6b4152d20288c7db4ef7d3927794`；變更只調整 Frontend，rules retrieval、Backend、資料庫、RAG、IAM、AWS資源與workflow均未修改。
- Red `1b284dc`、Browser corrective Red `0700ab0`、initial Green `8693e57`、jelly visual Red `8dfd379`、jelly visual Green `786dbae`；完整 Frontend regression `129/129`。
- Launcher已由帶小圖示的矩形按鈕改為半透明圓潤膠體、直接長在身體上的眼睛與微笑、底部果凍裙邊／偽足、陰影、跳動與提示泡泡；沒有深色螢幕臉或分離機械腳，底層仍保留原生button與ARIA。
- 390×844首頁／Demo、768×844、1440×900 Browser QA均無水平溢位或nav overlap；390 Demo的寵物與dialog不和composer／textarea相交。
- PR CI與merge後main CI均全綠；release run `33583003508`通過production approval、OIDC、ARM64 immutable image、digest fence、Trivy、bounded SSM與delivery metrics，active Web更新為`sha256:ad0ee896…`，previous `sha256:14d8e0f…`保留為rollback。
- 玩家可見production為`Release v1.1.1`。Browser驗證果凍本體、裙邊與直接表情存在，舊機器人面板／分離腿不存在，對話框可開啟且無水平溢位；strict TLS首頁／live／ready皆為`200`。每次玩家可見patch必須遞增SemVer patch並由regression test拒絕上一版號；docs-only commit不遞增。

## 2026-09-04～05 v1.1.2 與 Worker ToolUse hotfix

- PR #77 已將 `Release v1.1.2` 星火規則與展示 UI patch 合併至 `09dc09af12b3903f34aefe910699a066a3b56798`；main CI run `33844447220`、Web release run `33844595314` 均成功，active Web digest為 `sha256:c3e6c215…`。玩家目前仍看到 v1.1.2。
- PR #78 的 `Release v1.1.3` support dialog layout 已合併，並隨後包含於目前 repo main；它是後續另行展示的 Web release，尚未部署。Worker hotfix 不得改寫此版號或觸發 Tier 3 Web workflow。
- Production CloudTrail 將失敗 round 的三次 Worker 嘗試歸因為 Nova Lite `Converse` 的 `ModelErrorException`／invalid ToolUse sequence。PR #81 只為 Nova forced-tool request加入 `topK=1`，並將 Worker token budget由 `800`提高到 bounded `3000`；不修改 Web、DB、schema、IAM、Queue、Publisher或AWS資源。
- Worker artifact run `33897173518` 綁定 exact main `3246f2a…`，production approval、ARM64 immutable build／push、exact-digest Trivy `HIGH/CRITICAL` gate與manifest均成功；新 digest為 `sha256:1655de7a…`。
- 使用者透過 Systems Manager 逐台更新 `ip-10-20-20-170` 與 `ip-10-20-20-91`。雙 Worker postflight皆為service enabled／active、container running、restart `0`、mode `async`、max tokens `3000`、exact digest一致且registry auth absent。
- 第一版hotfix的bounded玩家測試：Round 01於第一次嘗試`applied`；Round 02則在三次嘗試後`failed`，dispatch與completion正常。Safe CloudWatch diagnostics對後兩次分別為`round_narrative_bounds`與`round_action_consequence_bounds`；第一個failure沒有diagnostic record。此為corrective部署前的歷史失敗與根因證據，不是當前production結論。
- PR #83 以strict TDD修正上述邊界不對齊：Nova可見的description要求更短文字，結構正確但超長的文字才會依句界壓縮；主敘事／玩家後果等硬上限只小幅調整為`720`／`280`，結構、玩家集合與canonical state錯誤仍fail closed。Exact main為`c5f3d038…`，CI run `33904289566`四項全綠。
- Worker artifact run `33904742833`建置並掃描exact digest `sha256:439059c4…`；雙Worker postflight皆通過。使用者對原Round 02只按一次手動重試，成功生成故事並進入Round 03。已修正本次觀察到的length-bounds失敗路徑；仍保留bounded retry／fallback，不宣稱Bedrock永不失敗。Web仍是v1.1.2，Publisher不變，v1.1.3仍待獨立展示部署。

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
- UI／像素 Support Widget production release與HTTPS恢復：[`docs/evidence/2026-09-01-ui-support-production-release/validation.md`](../evidence/2026-09-01-ui-support-production-release/validation.md)
- 寵物規則助手 production release：[`docs/evidence/2026-09-02-pet-rules-production-release/validation.md`](../evidence/2026-09-02-pet-rules-production-release/validation.md)
- 寵物視覺 v1.1.1 production release：[`docs/evidence/2026-09-02-pet-visual-v1-1-1-production-release/validation.md`](../evidence/2026-09-02-pet-visual-v1-1-1-production-release/validation.md)
- Nova Lite ToolUse Worker-only hotfix：[`docs/evidence/2026-09-05-bedrock-tooluse-hotfix/validation.md`](../evidence/2026-09-05-bedrock-tooluse-hotfix/validation.md)

## Next

1. 以現有 Tier 0–3、UI／寵物規則助手與bounded Support Agent production證據建立5–8分鐘final Demo；不重跑Bedrock、玩家E2E、synthetic incident或rules draft。
2. 整合 final production architecture 與課程能力對映；Tier 4／5 若保留於圖中，必須標示 `Future roadmap / Out of scope for final delivery`。
3. 建立 final evidence index，使 Demo 每一步只連到一個 canonical sanitized evidence。
4. 完成 repository secrets 掃描與 tracked screenshots OCR／人工遮罩 audit。
5. 以strict TDD把ACME父目錄最小穿越權限、公開challenge probe與憑證到期／renewal failure觀測固化至repo；不得放寬`/var/lib/co-story`的list／read／write權限。下一次timer成功前保留此項為residual，不重複手動renew。
6. 完成 2026-09-08 清理 runbook，列出現役資源、dependency order、ECR `Retain`、snapshot 決策、owner 與帳單複查方式；未取得人工指示前不執行清理。
7. 最後同步 README、architecture index、project plan、gantt與checkpoints；不得用歷史Tier 4／5未勾項覆蓋ADR-0008。
8. Tier 4／5、Support Agent Bedrock／RAG／external submit 都是 future scope；本UI patch不構成 AWS change envelope 擴張。

## 操作護欄

- Console-first；使用者操作 AWS Console／SSM。Agent 未經新的 bounded batch 核准不得執行 AWS CLI，且不得執行 S3 讀取或 Bedrock 呼叫。
- 保留 EC2 上所有 exactly-one markers，不重跑已完成的模型、incident、synthetic baseline 或第二回合 story job。
- 每次只提供一組同一目的、具停止條件的 Console／SSM 指令。
- 互動式 SSM Session 指令不得使用頂層 `exit`；若需要 exit code，使用 subshell，讓外層 Session 保持開啟。
- Protected file 的唯讀檢查必須使用 `sudo`；gate 失敗只輸出 `stopped` 與診斷摘要，不終止 Session。
- 指令與證據不得輸出 runtime.env、secrets、token、ARN、public IP、Email、account ID 或其他敏感值。
- 成本上限 USD 35，預定資源清理日 2026-09-08。

## Residual risks

- Direct IP certificate為短效憑證；2026-09-01曾因ACME webroot父目錄缺少Nginx穿越權限而過期，production ACL修復與人工bounded renewal已成功，新憑證到期日為2026-09-08。下一次timer自動renew尚未觀察，且repo尚未固化ACL／strict-TLS gate；EC2 stop／start若public IP改變，URL、certificate與allowlist都需重建。
- EC2 與 RDS 最近一次已知狀態均為運行中。RDS stop 後 storage／backup 仍可能計費，且最長 7 天會自動啟動。
- `CoStoryHealthCheck` 已通過正面 gate，尚未執行 Document 自身的代表性 failure gate。
- 尚未驗證多人長時間連續回合、iPhone Safari 長時間 polling／visibility，以及 `COMPLETED` 房間刪除後的 AWS 多分頁 lifecycle。
- ECR 保留歷史 fail-closed 與 successful release images，lifecycle limit 為 `10`；舊 runs 不得 re-run，storage／scan 仍可能產生少量費用。
- Support Agent static retrieval 無法涵蓋所有自然語言問法，identity digest 未加鹽；Bedrock／RAG／external submit 不在已部署的 bounded scope。
- 原始截圖若位於 TemporaryItems／Downloads 不算正式 evidence；入庫前必須去識別化。
