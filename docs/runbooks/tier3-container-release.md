# Tier 3 container release runbook

## 使用前提

本 runbook 只定義 bounded change envelope，不能視為 AWS 已部署。固定現況是 active legacy release `tier1-20260825-4a51e0e`、ECR 0 images、沒有 previous container digest。使用者尚未逐批核准前，Agent 不執行 AWS CLI、S3 讀取、Bedrock 呼叫、SSM、image push、`workflow_dispatch` 或 production deploy。

Production GitHub environment 必須設定 required reviewer；repository variables 只放 `AWS_REGION=ap-northeast-1`、ECR repository name、instance ID 與 deploy role ARN，不放 secrets。AWS 帳號若已有 `token.actions.githubusercontent.com` provider，部署 template 時傳入其 ARN，避免建立第二個 account-wide provider。

## 兩種 release mode

- `legacy-bootstrap`：只用於 `tier1-20260825-4a51e0e` 首次切換。`previous_image_digest` 必須空白，`expected_legacy_release` 必須精確相等；禁止假 digest、target digest 或相同 digest冒充 previous。
- `digest-release`：只用於已有 verified container state 的後續版本。必須提供與 target 不同、且同時吻合 root-only state 與 active release env 的 previous digest；不得提供 legacy release input。

兩種模式都只接受 main、production environment 人工核准、OIDC 短期憑證、ARM64 image、exact digest scan，Trivy 保持 `HIGH,CRITICAL` 與 `exit-code: 1`。Migration 不提供 downgrade；每個 migration 在 release 前必須證明舊 runtime 可讀取新 schema，否則不得批准。

## Change Set 與主機 preflight

使用者先在 CloudFormation Console 建立 Change Set，只接受下列預期變更：更新 `CoStoryTier3ContainerRelease` 的新 document version，並新增 `CoStoryTier3LegacyRollback`。若出現 GitHub role 權限擴張、App role 擴張、ECR replacement、instance replacement 或其他資源，立即停止且不執行 Change Set。GitHub deploy role 只能執行 release document，不能執行 legacy rollback document。

Change Set 執行完成後，使用者另開一批 Console／SSM read-only preflight：確認 Docker 已安裝且 active、固定 legacy symlink／unit／`live`／`ready` 正常、runtime 與 database env metadata 為 `root:co-story:640`，且 container state、release env、legacy backup 都不存在。Docker 未安裝、ECR 仍為空或 Change Set 未套用，都只是停止條件，不得跳過 guard。

## First transition gate

1. 指定合併後、已全綠的 exact main SHA；production reviewer 必須核對 SHA、mode、固定 legacy release、Region、repository、instance 與 rollback envelope。
2. Workflow build／push ARM64 immutable image，對 build output 的 exact digest 執行 Trivy；scan 未通過即停止，不得新增 ignore／VEX／skip 或降低 gate。
3. SSM bootstrap 在第一次 pull 前再次驗證 symlink、legacy unit checksum、legacy health、env metadata，以及沒有既有 container state／release env；任一不符即在 mutation 前 fail closed。
4. Document 只從 exact scanned digest 建立暫時 container，複製 image 內固定 driver 與 container unit；不得下載任意 URL，也不得依賴 active legacy release 裡不存在的 Tier 3 script。
5. 順序固定為 exact digest pull → migration → legacy `live`／`ready` 再驗證 → target candidate `:8001` `live`／`ready` → 原子保存 legacy unit、checksum、release 與 root-only transition state → 切換 target `:8000`。
6. Migration 後 legacy 不再 ready，視為 backward-compatible gate 失敗；保持 legacy unit，不切換。Candidate 失敗亦不切換。
7. Target restart 或 health 失敗，原子恢復 exact legacy unit、`daemon-reload`、restart 並驗證。Restore 失敗必須 nonzero 且保存 `legacy-restore-failed`，不得宣告成功。
8. 只有 SSM 回傳 `container_release=verified`，且 public edge 的 `/live`、`/ready` 都是 200，才算完成；成功 state 保存 exact active digest、legacy release、legacy／container unit checksum。

## 後續 digest release

後續 release 在 login、pull、migration 之前，會核對 state metadata／shape、active env、installed unit checksum、固定 container unit asset checksum與 previous digest。任何不一致都停止。通過後仍依序執行 migration、previous runtime schema-compatible health、target candidate 與 target switch；target 失敗須恢復 previous exact digest，restore 失敗明確 nonzero。這條路徑不降級既有 digest-to-digest rollback。

## 人工 legacy rollback

`CoStoryTier3LegacyRollback` 只能由使用者在 Console／SSM 單獨操作，輸入 exact active digest 與固定 legacy release。它先核對 root-only state、active env、unit／backup checksum，再以固定 `/opt/co-story/releases/tier1-20260825-4a51e0e/.venv/bin/uvicorn` 啟動 transient systemd candidate，在 `:8001` 驗證 legacy 對現行 schema仍可讀。失敗不切換；切換 legacy 後若 `:8000` 不健康，必須恢復原 container unit與 exact active digest。兩條 rollback 都不執行 schema downgrade。

## Release gate

1. 確認 exact main commit 已通過 Backend、Frontend、container build 與 HIGH／CRITICAL scan。
2. 首次 transition 選 `legacy-bootstrap`；後續 release 才能選 `digest-release` 並輸入目前已驗證的 previous digest。
3. 從 exact main SHA 手動啟動 `Tier 3 container release`，輸入與 mode 相符的互斥參數。
4. Required reviewer 核對 commit、target／previous digest、instance、Region 與 rollback 後批准 production environment。
5. Workflow 以 OIDC build／push immutable commit tag，掃描 exact digest，再透過 `CoStoryTier3ContainerRelease` 發送 bounded SSM command。
6. 只有 SSM 回傳 `container_release=verified` 且 public Nginx edge 的 `/live`、`/ready` 都為 200 才算完成。
7. 無論成功或失敗，下載 `tier3-delivery-metrics-<run-id>` artifact，依[量測方法](../evidence/2026-08-26-tier3-delivery/deployment-efficiency-method.md)保存原始值；artifact 不取代 AWS health evidence。

## 停止條件

- previous digest 不符 active release：停止，不覆寫主機狀態。
- legacy release、symlink、unit checksum、env metadata、transition state 或 release env 不符：在 mutation 前停止。
- Docker 未安裝／未 active、ECR 沒有已掃描 target digest或 Change Set 未完成：停止。
- migration、candidate 或 target health 失敗：停止；target 未啟用或自動恢復 previous digest。
- legacy／previous restore health 仍失敗：保留 nonzero state並停止；不得覆寫 state、關閉 guard或直接重試 deploy。
- public edge 與 instance health 不一致、SSM timeout／nonzero、scan digest 與 deploy digest 不一致：停止。
- Rollback 不降版 PostgreSQL schema；所有 Tier 3 migration 必須先證明 previous image 可讀新 schema。

## 成本與清理

新增費用面只有 ECR 儲存與 scan；repository lifecycle 只保留最新十個 image。OIDC、IAM role 與 SSM Document 本身不建立常駐 compute。CloudFormation 對 ECR 設 `Retain`，清理前必須先由使用者確認保留的 rollback digest。
