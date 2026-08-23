# Tier 1 受限 SSM 健康檢查驗證摘要

- Scope／risk／upstream source：R3 IaC；依 `AGENTS.md`、Tier 1 SSM 免 SSH 目標與專題 Skill 的最小權限邊界。
- Baseline：既有 Tier 1 observability contract `8 passed`；Backend `325 passed, 8 skipped`。
- Red commit：`f854723`；targeted `5 failed`，皆因 `tier1-ssm-health-check.yaml` 尚未建立。
- Green commit：`3dd8a84`；建立單一 `AWS::SSM::Document`，不建立 IAM、Association、排程或自動修復資源。
- Targeted verification：SSM health-check contract `5 passed`。
- Affected verification：observability＋SSM contracts `13 passed`。
- Full regression：Backend `330 passed, 8 skipped`。
- Positive：固定檢查 `co-story.service`、loopback `/live` 與 `/ready`，成功輸出只包含三個安全狀態。
- Negative／boundary：文件無操作者參數、無 `{{ }}` interpolation、無 AWS managed `AWS-RunShellScript` reference、無 restart／AWS CLI／外部 URL／runtime 設定輸出。
- Sensitivity：加入自由 `Commands` parameter、加入 service restart、移除 readiness、移除 `DeletionPolicy` 四種 mutation 均被對應測試抓到並已還原。
- Local syntax：CloudFormation YAML 可解析，組合後的固定 Bash commands 通過 `bash -n`。
- Rollback：stack delete 移除文件；`UpdateMethod: NewVersion` 保留可切換的文件版本，不改動 EC2 runtime。
- Residual risk：尚未執行 CloudFormation Change Set／AWS schema validation／實機 Run Command；部署前仍須確認 principal、Region、managed instance、instance profile 與限定文件的 operator permission。
