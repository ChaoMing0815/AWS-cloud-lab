# Tier 3 container release runbook

## 使用前提

本 runbook 只定義 bounded change envelope，不能視為 AWS 已部署。固定現況是 active legacy release `tier1-20260825-4a51e0e`、ECR 0 images、沒有 previous container digest。使用者尚未逐批核准前，Agent 不執行 AWS CLI、S3 讀取、Bedrock 呼叫、SSM、image push、`workflow_dispatch` 或 production deploy。

Production GitHub environment 必須設定 required reviewer；repository variables 只放 `AWS_REGION=ap-northeast-1`、ECR repository name、instance ID 與 deploy role ARN，不放 secrets。AWS 帳號若已有 `token.actions.githubusercontent.com` provider，部署 template 時傳入其 ARN，避免建立第二個 account-wide provider。

`TIER3_INSTANCE_ID` 必須是無任何前後空白的 canonical EC2 instance ID，且精確符合 `^i-[0-9a-f]{17}$`。Workflow 必須在取得 AWS credentials 與 build 之前驗證 raw repository variable；不得靜默 trim。只有通過驗證後寫入的 `VALIDATED_TIER3_INSTANCE_ID` 可供 SSM send／wait／get 共用。

## 四種 release mode

- `legacy-bootstrap`：只用於 `tier1-20260825-4a51e0e` 首次切換。`previous_image_digest` 必須空白，`expected_legacy_release` 必須精確相等；禁止假 digest、target digest 或相同 digest冒充 previous。
- `digest-release`：只用於已有 verified container state 的後續版本。必須提供與 target 不同、且同時吻合 root-only state 與 active release env 的 previous digest；不得提供 legacy release input。它從 canonical installed unit 精確繼承目前 `sync|async` resolution mode，不接受 target source unit 覆蓋 active mode。
- `migration-bridge`：只用於將 active digest 切換成可讀舊 schema的同步 bridge。previous 必須是 canonical active digest、legacy input 必須空白；全程不執行 migration，candidate 與 stable runtime 都固定 sync。成功後才寫入 root-only digest-bound bridge marker。
- `schema-activation`：只能以 marker 綁定的 verified bridge digest 為 previous；先驗 marker，再 migration、重驗 marker、驗 bridge runtime與candidate。任何失敗只回復 bridge runtime，不做 schema downgrade。

`schema-activation` 的 `preflight-only` 必須只驗證 bridge marker，並完整保留其內容、`root:root:0600` metadata 與 digest binding；只有同一次完整 release 在 migration、candidate、target activation及canonical state全部成功後才可移除 marker。若舊版driver在preflight誤刪marker，立即停止，不得重跑失敗workflow或手動偽造marker；先確認active digest仍是verified bridge、migration inventory未前進且runtime health正常，再以獨立核准的bounded recovery恢復marker。

所有 mode 都只接受 main、production environment 人工核准、OIDC 短期憑證、ARM64 image、exact digest scan，Trivy 保持 `HIGH,CRITICAL` 與 `exit-code: 1`。未知 mode 或互斥 input 必須在 credentials、build、registry、migration 或 mutation 前停止。Migration 不提供 downgrade；每個 migration 在 release 前必須證明 verified bridge runtime 可讀取新 schema，否則不得批准。

## Migration bridge bootstrap compatibility

已存在的舊stable driver只理解`digest-release`，因此migration bridge的pull前只能以該mode和`preflight-only`執行common host／active digest／checksum fence；target digest仍是新image digest，previous仍是canonical active digest，asset參數只能是既有stable driver與unit。此步不登入registry、不pull、不遷移也不改寫host state。

Document之後才pull exact scanned digest、以該digest建立asset container，並在root-owned `0700` temporary directory擷取target driver與unit。`migration-bridge`與`schema-activation`都要檢查temporary directory、兩個asset的canonical regular-file／non-symlink／`root:root:0500`或`root:root:0400`metadata、container image ID與pulled image ID一致，並在target preflight前後比對兩個SHA-256。兩種mode各自只能由同一份temporary target driver完成preflight與release。schema activation在registry access前另由Document只讀驗證root-only marker的兩行shape、state與previous digest binding，不呼叫可能仍是舊版的host stable driver；target preflight必須保留marker，完整release成功後才可清除。

任何extract或preflight失敗只清除Document自己的asset container與temporary directory，不得變更active runtime、verified marker或release state。target driver已進入mutation後的失敗仍依既有rollback恢復previous runtime；restore失敗保留root-only forensic state並停止。這個repo-local corrective合併與CI完成前，不得建立或執行Change Set。

bridge candidate通過後，target driver先保存previous stable driver／unit、寫入pending state與target release env；只有`migration-bridge`才可在首次target restart前重新驗target unit source SHA-256、原子安裝已驗證target unit到installed systemd unit（`root:root:0644`）、再驗destination SHA-256並執行`daemon-reload`。首次target health前stable driver與stable unit仍維持previous版本。health通過後才promotion stable assets、再次restart／health、寫canonical active state，最後才寫verified bridge marker。handoff、hash、reload、restart、promotion或health任一步失敗都必須由previous backups恢復installed／stable assets、release env與previous runtime；restore失敗保留既有root-only forensic state。`digest-release`與`schema-activation`不得採用此handoff。

`migration-bridge`與`schema-activation`的container unit resolution mode仍固定為精確的`Environment=CO_STORY_RESOLUTION_MODE=sync`。`digest-release`則只從目前 canonical installed unit 讀取唯一精確的`Environment=CO_STORY_RESOLUTION_MODE=sync|async`；missing、duplicate、空值、空白、大小寫或未知值都必須在registry login、pull、migration及service／state mutation前停止。驗證後的同一mode必須供target candidate使用，並綁定到promotion的installed／stable target unit；失敗rollback恢復的previous unit也必須保持該mode。systemd的Environment只影響Docker CLI process，並不會自動進入container，因此同一個`ExecStart`必須以相鄰token `--env CO_STORY_RESOLUTION_MODE=${CO_STORY_RESOLUTION_MODE}`顯式傳入allowlisted、非秘密值。不得把此值放進`runtime.env`或`container-release.env`，也不得在Docker參數硬編第二份mode。

## Change Set 與主機 preflight

使用者先在 CloudFormation Console 建立 Change Set，只接受下列預期變更：更新 `CoStoryTier3ContainerRelease` 的新 document version，並新增 `CoStoryTier3LegacyRollback`。若出現 GitHub role 權限擴張、App role 擴張、ECR replacement、instance replacement 或其他資源，立即停止且不執行 Change Set。GitHub deploy role 只能執行 release document，不能執行 legacy rollback document。

Change Set 執行完成後，使用者另開一批 Console／SSM read-only preflight：確認 Docker 已安裝且 active、固定 legacy symlink／unit／`live`／`ready` 正常、runtime 與 database env metadata 為 `root:co-story:640`，且 container state、release env、legacy backup 都不存在。Docker 未安裝、ECR 仍為空或 Change Set 未套用，都只是停止條件，不得跳過 guard。

Host 的 `/etc/pki/rds/rds-ca.pem` 必須是 canonical regular file、不得是 symlink、owner/group 為 `root:root`、app user 可讀，且 group／other 不可寫。SSM Document 在第一次 ECR login／pull 前及 release driver common preflight 都要再次檢查；不符合即停止。CA 不得 COPY／ADD 進 image，也不得降低 PostgreSQL `verify-full`。

Container image的default user維持非root `10001:10001`，但production host的固定log allowlist沿用既有`co-story` identity。Release driver必須以`id -u/-g co-story`取得canonical非零numeric UID/GID，不得硬編host實際值。Candidate與stable runtime使用該identity；migration仍維持既有非root與TLS邊界。`/var/log/co-story`必須是非symlink canonical directory且numeric metadata精確為validated UID/GID與`750`；既有`candidate.jsonl`必須是regular、非symlink、同identity所有、`640`且該identity可寫。任何不符在candidate前停止。

## First transition gate

1. 指定合併後、已全綠的 exact main SHA；production reviewer 必須核對 SHA、mode、固定 legacy release、Region、repository、instance 與 rollback envelope。
2. Workflow build／push ARM64 immutable image，對 build output 的 exact digest 執行 Trivy；scan 未通過即停止，不得新增 ignore／VEX／skip 或降低 gate。
3. SSM bootstrap 在第一次 pull 前再次驗證 symlink、legacy unit checksum、legacy health、env metadata，以及沒有既有 container state、release env、legacy backup或 stable assets；任一不符即在 mutation 前 fail closed。
4. Document 只從 exact scanned digest 建立暫時 container，複製 image 內固定 driver 與 container unit；不得下載任意 URL，也不得依賴 active legacy release 裡不存在的 Tier 3 script。Final image 只建立 root-owned `/etc/pki/rds` 空 mountpoint；migration、candidate `:8001` 與 stable systemd container都把 host CA readonly bind mount至相同 absolute path。
5. 順序固定為 exact digest pull → migration → legacy `live`／`ready` 再驗證 → target candidate `:8001` `live`／`ready` → 原子保存 legacy unit、checksum、release 與 root-only transition state → 切換 target `:8000`。
6. Migration 後 legacy 不再 ready，視為 backward-compatible gate 失敗；保持 legacy unit，不切換。Candidate 失敗亦不切換。
7. Candidate失敗時，只能在移除container前用bounded inspect format輸出`running/exited`等sanitized state與numeric exit code；不得輸出raw logs、完整inspect、env、registry URI或secret。
8. Backup、stable asset、state、release env、unit install或 `daemon-reload`任何一步失敗，都要精確恢復 legacy unit、reload、restart並驗證 health，再逐一清除本次建立的五個 transaction files；乾淨恢復後可用相同 exact inputs安全重試。
9. 若 mutation restore或精確 cleanup本身失敗，保留 mode `0600`的 `legacy-mutation-restore-failed` state與 nonzero結果；不得自動重試或刪除 failure state。程序 crash若留下 pending／checksum不一致也一律 fail closed，等待人工判讀。
10. Target restart或 health失敗走相同 rollback；不得吞錯或宣告成功。
11. 只有 SSM回傳 `container_release=verified`，且 public edge的 `/live`、`/ready`都是 200，才算完成；成功 state保存 exact active digest、legacy release、stable driver及 legacy／container unit checksum。Root-only release env必須精確三行保存active image與validated UID/GID；missing、duplicate、額外key、非numeric、root值、metadata或host identity mismatch都在digest-release與legacy rollback mutation前停止。

## 後續 digest release

後續 release在任何 target pull前，先由目前 active stable driver核對 state metadata／shape、active env、stable driver checksum、stable／installed unit checksum、暫存 backup不存在、previous digest，以及canonical installed unit中唯一的active resolution mode。任何不一致都停止。Document之後才從 exact scanned target digest擷取本次 driver與unit到暫存區，不使用任意 URL。

通過後依序執行 migration、previous runtime schema-compatible health、使用validated active mode的target candidate，以及使用目前stable unit的第一次target switch。新driver／mode-bound target unit在target `:8000`健康前不得永久安裝；其後先保存previous stable assets與pending state，再原子promotion、`daemon-reload`、以同一validated mode的新unit restart target並再次驗證`target-promoted` health，最後才寫入新checksum與active state。Promotion或第二次health失敗，必須恢復previous stable driver、unit、installed unit、同一active mode與exact previous digest；restore失敗保存`asset-restore-failed`並nonzero。Crash留下pending state、backup或checksum漂移時fail closed。這條路徑不降級既有digest-to-digest rollback。

## 人工 legacy rollback

`CoStoryTier3LegacyRollback`只能由使用者在 Console／SSM單獨操作，輸入 exact active digest與固定 legacy release。它先核對 root-only state、active env、stable driver、stable／installed unit與legacy backup checksum，再以固定 `/opt/co-story/releases/tier1-20260825-4a51e0e/.venv/bin/uvicorn`啟動 transient systemd candidate，在 `:8001`驗證 legacy對現行 schema仍可讀。失敗不切換；切換 legacy後若 `:8000`不健康，必須恢復原 container unit與 exact active digest。兩條 rollback都不執行 schema downgrade。

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
- `TIER3_INSTANCE_ID` 含前後空白、換行、Tab、長度或大小寫不符 canonical regex：在 credentials／build 前停止，不得 trim後繼續。
- RDS CA 缺少、是 symlink、非 canonical regular file、app不可讀或 group／other可寫：在第一次 login／pull前停止，不得複製CA進image或降低TLS。
- Host `co-story` UID/GID不是canonical非零numeric值，或log directory／candidate log的type、symlink、owner、`750/640` mode與實際可寫性不符：candidate前停止，不得改成`777`、group/other writable或關閉file logging。
- Root-only release env不是精確image／UID／GID三行，metadata不是`root:root:600`，或identity不符host：digest-release與legacy rollback在mutation前停止。
- Canonical installed unit缺少、重複或包含非精確`sync|async`的resolution mode：digest-release在registry login、pull、migration與任何service／state mutation前停止，不以source unit預設值繼續。
- migration、candidate 或 target health 失敗：停止；target 未啟用或自動恢復 previous digest。
- legacy／previous restore health 仍失敗：保留 nonzero state並停止；不得覆寫 state、關閉 guard或直接重試 deploy。
- `legacy-switch-pending`、`digest-switch-pending`、`asset-promotion-pending`、任何 `*-failed` state、previous asset backup殘留或 stable asset checksum漂移：停止並交由人工處置。
- public edge 與 instance health 不一致、SSM timeout／nonzero、scan digest 與 deploy digest 不一致：停止。
- Rollback 不降版 PostgreSQL schema；所有 Tier 3 migration 必須先證明 previous image 可讀新 schema。

## 成本與清理

新增費用面只有 ECR 儲存與 scan；repository lifecycle 只保留最新十個 image。OIDC、IAM role 與 SSM Document 本身不建立常駐 compute。CloudFormation 對 ECR 設 `Retain`，清理前必須先由使用者確認保留的 rollback digest。
