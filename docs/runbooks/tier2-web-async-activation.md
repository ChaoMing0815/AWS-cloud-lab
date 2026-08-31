# Tier 2 Web async activation 與 rollback envelope

- 狀態：Production activation、rollback與玩家exactly-one E2E均已完成
- Envelope 名稱：`tier2-web-async-activation-b9c8b84-20260831`
- Region：`ap-northeast-1`
- 成本上限：USD 35
- 預定清理日：2026-09-08

## 目的與既有基準

本 envelope 只界定玩家 Web 從精確 `sync` 切換為 `async`，以及失敗時回復 `sync` 的單一 production 變更。它不授權執行 AWS 操作、建立測試工作或呼叫 Bedrock。

最終執行基準為 PR #63 merge commit `bf7de1f4bd8dbb6e3f6791c3160a0532bbe5820f`。目前 production 基準如下：

- Web 與 publisher image：`sha256:23357e315e94842cee8455023b1f87f203fca5b1d11b67b714f4af86efaa2a1b`
- Web：service active、container running、`CO_STORY_RESOLUTION_MODE=async`
- Publisher：static unit、service active、container running
- 兩台 private Worker：`sha256:2d5d5866f54879e79882644f4b45af2475650ddc9972e6b91cfe786886cddfbc`，service active、container running、restart `0`、mode `async`
- Migration inventory：精確 `001`–`005`
- 主 Queue 與 DLQ：available、in-flight、delayed、DLQ available 均為 `0`
- Exactly-one synthetic E2E：單一 job、單次 dispatch、最多一次 Bedrock invocation，結果 `applied`，Room 回 `COLLECTING_ACTIONS`；marker 已清除

任何基準不符都必須停止，不得以「已在前次驗證」略過本次會受 activation 影響的 runtime 狀態。

## 允許的變更

Activation batch 只允許：

1. Web service 的單一 canonical mode 由 `sync` 改為 `async`，並把同一值顯式傳入 Web container。
2. 更新與該 Web unit 一致的 root-only checksum／transition state，保留既有 exact image、UID、GID與release state不變。
3. `daemon-reload`、重啟 Web service，驗證 container、internal health 與 public edge。

不得改變：

- Web／publisher／Worker image digest
- Publisher 或兩台 Worker 的 service 狀態與runtime設定
- SQS、DLQ、RDS schema、IAM、Security Group、NAT、CloudFormation resource 或任何其他AWS資源
- `runtime.env`、`database.env`、secret、TLS、Nginx、session／CSRF與public URL
- 玩家請求、job、SQS message或Bedrock invocation；這些屬 activation 後的獨立玩家 E2E batch

若實作需要新 image、SSM Document、IAM action、CloudFormation change、額外 compute 或持續計費資源，此 envelope 立即失效，必須另列 delta 並重新核准。

## 必要 delivery contract

不得直接用 `sed`、Console editor或未版本化的臨時指令修改 installed unit。執行 activation 前，repo 必須先以 strict TDD 提供版本化、fail-closed 的 mode transition contract，至少證明：

- 只接受 literal `sync → async` 與 `async → sync`；大小寫、空白、未知值與same-mode一律在mutation前停止。
- 同時核對 installed unit、stable unit、transition state、release env、active digest與service健康；checksum或metadata漂移即停止。
- 先保存 exact previous unit，原子安裝target unit，執行`daemon-reload`、restart及bounded health gate。
- 任一 mutation／restart／health失敗，自動恢復 exact previous `sync` unit、reload、restart並再次驗證health。
- Restore失敗保留root-only forensic state並nonzero停止；不得自動重跑或覆寫failure state。
- 成功後更新canonical checksum/state，且不把mode寫入secret-bearing env file。

Repo-local contract 位於[`ops/release/transition_web_resolution_mode.sh`](../../ops/release/transition_web_resolution_mode.sh)，只接受三個參數：`activate|rollback`、目前active Web image digest及既有public health host。它不呼叫AWS API、不登入registry、不讀取或輸出runtime／database env內容，也不建立job或message。執行時必須從已合併、CI全綠的exact main完整複製該檔案內容，以`sudo bash -s -- <action> <digest> <health-host>`透過Console的`AWS-RunShellScript`送達單一既有Web EC2；不得從任意URL下載、局部貼上、手動patch或把檔案永久寫入host。

Script會核對root權限、三個參數、active digest、release env、七行canonical state、installed／stable unit、stable driver、metadata、checksum、service、container、restart count、container mode及internal／public live／ready。它只原子替換unit的唯一mode來源並更新canonical unit checksum；release image、UID、GID及其他state欄位保持不變。成功輸出只能是`web_async_activation=verified previous=sync current=async`或`web_async_rollback=verified previous=async current=sync`；失敗只輸出allowlisted reason。

上述 contract 已由PR #59、#61、#62與#63逐步完成candidate、failure diagnostics及bounded startup polling修正；最終PR #63四項CI全綠後才執行production activation。

## Activation preflight

一次 preflight 必須在 mutation 前全部通過，輸出只保留下列 sanitized 摘要：

- exact main SHA、active Web digest與root-only release state互相吻合
- installed／stable unit checksum吻合，沒有pending／failed transition或backup殘留
- Web service active、container running、restart `0`、internal live／ready與public live／ready均為`200`、mode精確`sync`
- Publisher active／running；兩台Worker均active／running／restart`0`且digest精確吻合上述基準
- migration inventory精確`001`–`005`
- 未完成StoryJob、未完成dispatch outbox、未完成completion outbox與test marker均為`0`
- 主Queue與DLQ的available／in-flight均為`0`

不得輸出secret、DSN、token、ARN、玩家內容、public IP、runtime env內容或完整systemd unit。

## Activation 成功條件

只有全部符合才可回報成功：

- mode transition回`web_async_activation=verified previous=sync current=async`
- Web service active、container running、restart `0`
- container內有效mode精確為`async`
- internal live／ready及public live／ready均為`200`
- Publisher與兩台Worker維持既有active／running狀態及exact digest
- activation本身未建立job、message或Bedrock invocation；主Queue／DLQ仍為空
- canonical release state沒有pending／failed狀態或backup殘留

任何一項不同都視為 activation 失敗，必須依 rollback boundary 回復 `sync`，不得進入玩家 E2E。

## Rollback boundary

Rollback 是同一 delivery contract 的明確 `async → sync` 路徑，不做 schema downgrade，也不回復較舊 application image。步驟必須：

1. 在mutation前核對active digest、current mode `async`、unit／state checksum與服務健康。
2. 原子恢復已驗證的canonical `sync` unit，`daemon-reload`並restart Web。
3. 驗證container mode `sync`、service active、restart `0`、internal/public live與ready均為`200`。
4. 驗證Publisher與Worker未變，主Queue／DLQ仍為空，沒有新增test marker。
5. 回報`web_async_rollback=verified previous=async current=sync`。

Rollback失敗時保留root-only forensic state並停止；不得反覆restart、手動改unit、清除state或啟動玩家測試。

Script執行成功會移除本次transaction backup；若target失敗且restore成功，會精確恢復原unit與原state並移除backup。若restore任一步失敗，保留`STATE=web-mode-restore-failed`及兩個root-only backup，等待人工判讀；若成功切換後backup cleanup失敗，保留`STATE=web-mode-cleanup-failed`並停止，不得重跑。

## 停止條件

下列任一情況立即停止並回報差異：

- mode、digest、schema inventory、service、container、checksum、metadata或queue baseline不符
- 存在未完成job／outbox、test marker、pending／failed transition或previous backup
- 需要修改image、IAM、CloudFormation、network、database schema、Publisher或Worker
- activation／rollback會輸出敏感值，或無法證明exact previous unit可恢復
- internal與public health不一致、SSM nonzero／timeout，或rollback health未恢復
- 成本可能超過USD 35，或清理責任／2026-09-08清理日改變

## 後續獨立關卡

Activation成功後已另行取得production核准並完成受控玩家流程。首次單一job以一次dispatch／一次Bedrock invocation回`TRANSIENT_SERVICE_ERROR`，依本runbook回復`sync`；第二個另行核准的人工retry同樣限制為一次dispatch／一次invocation，結果`applied`並進入Round 02／`COLLECTING_ACTIONS`。兩批均沒有自動重跑。

## 成本與清理

本activation本身不建立新資源，預期不增加固定費用；既有兩台Worker、EBS、NAT Gateway、EIP、RDS、EC2、CloudWatch與ECR仍持續計費。後續玩家E2E只允許另行核准的最多一次Bedrock invocation。成本上限USD 35與2026-09-08清理日不變；清理時只保留可快速重建所需的repo、IaC、immutable manifest與sanitized evidence。
