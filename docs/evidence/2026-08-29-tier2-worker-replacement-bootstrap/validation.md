# Tier 2 Worker replacement bootstrap validation

- Base：`aa083ea2cc5e17d1a29ba4299f117ba837fbdc5a`
- Branch：`codex/tier2-worker-replacement-bootstrap`
- 風險：R3 Launch Template／ASG rolling replacement

## 邊界與結果

- Resource inventory仍精確20；未新增IAM、NAT、compute、Queue或其他resource。
- 新增exact image digest與private RDS endpoint參數；UserData不含secret value，只保存既有exact secret ARN。
- 新instance由exact digest安裝hardened Worker；container active且35秒idle、restart count 0後才送CloudFormation success signal。
- ASG一次只替換1台、至少保留1台；signal失敗即讓CloudFormation update fail closed／rollback。
- Targeted：`16 passed`；Backend完整regression：`718 passed, 16 skipped, 1 existing warning`；`git diff --check`通過。
- Repo-local基線完成時未建立Change Set、未替換instance、未傳送message或呼叫Bedrock。

## 首次AWS更新與修正

- 使用者在Console確認Change Set只有`WorkerLaunchTemplate`與`WorkerAutoScalingGroup`兩項Modify、Replacement均為False，並明確核准執行。
- 更新因ASG只收到1/2成功signal而失敗；stack完成`UPDATE_ROLLBACK_COMPLETE`，Web仍維持sync且未啟用async。
- Rollback後一台Worker正常、一台replacement host沒有Docker；SSM部署輸出為`docker: command not found`，因此沒有重跑Change Set。
- 使用者只對該replacement host安裝並啟用Docker後重跑既有exact-digest部署；結果為`worker_release=verified`，digest仍為`sha256:ede0f8e571824e2b1100a537795825ecdff415b0dbd1fcbc1e8a1ebd50bf1757`。
- Red `f35c83c`證明三套件綁在同一`dnf install`會違反Docker獨立安裝邊界；Green `89e7703`先安裝Docker／curl，只在缺少`cfn-signal`時安裝`aws-cfn-bootstrap`。
- 修正後IaC targeted為`8 passed`；完整Backend gate exit 0；代表性mutation重新綁定三套件時targeted test如預期失敗，還原後通過。
- 修正模板仍精確20 resources，SHA-256為`94f7724adc115ac8404ab925a462f1f11addc2ba914fe8c1b68ddc1758c3dd7a`；未新增IAM、NAT、compute或Queue。
- Residual risk：此修正尚未在AWS replacement更新驗證；新的Change Set必須維持0 Add／0 Remove且僅上述2項Modify；若ASG因動態Launch Template version顯示`Conditional`，只接受既定三項property diff並另行取得執行核准。

## 第二次AWS更新與bounded readiness

- 第二個Change Set仍只有`WorkerLaunchTemplate`與`WorkerAutoScalingGroup`兩項Modify；ASG的`Conditional`只涉及`LaunchTemplate.Version`、`UpdatePolicy`與`CreationPolicy`，使用者明確核准後執行。
- 更新再次因1/2 failure signal而rollback；新instance在約第74秒由cloud-init `scripts-user`回報失敗，且已建立第三個Worker log stream但沒有log events。
- 證據只能把失敗定位到晚期health／signal階段，不能區分一次性readiness或signal瞬斷；因此沒有第三次AWS重試，也沒有假造根因。
- Red `85c05dd`要求bounded readiness、有限success signal retry與不含secret的固定phase／service diagnostics；Green `7f1a1ce`將單次35秒檢查改為最多120秒等待與3次signal。
- 修正後IaC targeted為`9 passed`；完整Backend gate exit 0；將readiness縮為單次的代表性mutation如預期被測試攔截，還原後通過。
- 模板仍精確20 resources，SHA-256為`6e299869df24154056caf67788d50644bcf0419c0f90ce4986bd06bc972636ea`；未新增IAM、NAT、compute、Queue或async activation。
- Residual risk：晚期失敗的精確外部原因仍未知；新模板的目的同時是容忍bounded transient並在再次失敗時留下可操作診斷，AWS執行仍需新的Change Set與明確核准。

## 第三次AWS更新與curl-minimal根因

- 第三個Change Set仍符合相同2-Modify envelope，但更新再次rollback；新增診斷精確輸出`phase=install_packages status=1`且Worker service尚未啟動。
- cloud-init原始錯誤證明AL2023預裝`curl-minimal`與UserData要求安裝的完整`curl`套件衝突；`dnf`因此整批失敗，這是先前三次rollback的實證根因。
- 修正不採用`--allowerasing`或`--skip-broken`；Red `7c0d5af`要求保留AL2023基礎套件，Green `7d87988`只安裝Docker並顯式驗證既有curl binary。
- 修正後IaC targeted為`9 passed`、UserData shell syntax通過、完整Backend gate exit 0；把完整curl加回`dnf`的代表性mutation如預期被攔截。
- 模板仍精確20 resources，SHA-256為`d220479dbaa01be1a47404e151458faac3c5ef42bf770e22b2ca4c46502d05d3`；IAM、network、compute、Queue、成本上限與sync／async邊界均未變更。
- Residual risk：最小修正尚未在AWS replacement驗證；不得沿用已執行失敗的Change Set，合併後需建立新的Change Set並另行核准。

## 最終AWS replacement驗證

- PR #44合併exact main `49bfb0e888b899ffda4b3868c1055ff5e41ea383`後，使用者建立並檢查`0 Add／2 Modify／0 Remove` Change Set；Launch Template為`Replacement=False`，ASG的`Conditional`只涉及既定三項property diff。
- 使用者在相同USD 35上限、2026-09-08清理日、Web維持`sync`且不啟用async的envelope內明確核准執行。
- Stack、`WorkerLaunchTemplate`與`WorkerAutoScalingGroup`均為`UPDATE_COMPLETE`；ASG Desired／In service為`2／2`。
- 兩個success signals只會在exact image、Worker service active、container running且restart count 0後送出，因此不重複執行相同SSM runtime驗證。
- 最終resource inventory仍精確20；沒有新增IAM、NAT、compute、Queue、message、Bedrock呼叫或玩家可見async行為。
- Replacement-safe Worker runtime已完成；剩餘Tier 2核心缺口為producer publisher／reconciliation、核准的AWS message E2E與後續獨立async activation。
