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
- Residual risk：此修正尚未在AWS replacement更新驗證；新的Change Set必須維持0 Add／0 Remove、僅上述2項Modify且Replacement=False，另行取得執行核准。
