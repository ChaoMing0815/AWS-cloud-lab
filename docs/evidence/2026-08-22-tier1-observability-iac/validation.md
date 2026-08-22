# Tier 1 Log Group 與最小寫入權限 IaC 驗證摘要

- Scope／risk／upstream：R3 IAM、成本與清理；依 `docs/architecture/tier1-minimum-gap-analysis.md` 建立 repo-local CloudFormation contract，未 deploy。
- Baseline：Backend `317 passed, 8 skipped`，工作樹乾淨。
- Red：`9c50ec4` 定義固定 Log Group、7 天 retention、單一 instance stream 與禁止額外服務；`ad4bc05` 補上禁止 `Users`／`Groups` principal 擴張。
- Green：`2250bd3`；template 只含 `AWS::Logs::LogGroup` 與 `AWS::IAM::ManagedPolicy`。
- Targeted／affected：`20 passed`（Tier 1 IaC、Agent contract、Tier 0 compute 與 IAM bootstrap）。
- Full regression：Backend `323 passed, 8 skipped`。
- IAM boundary：只允許精確 group 的 `DescribeLogStreams`，以及精確 `${AppInstanceId}` stream 的 `CreateLogStream`／`PutLogEvents`；不含 `CreateLogGroup`、`PutRetentionPolicy`、AWS managed full policy 或 wildcard resource。
- Cost／rollback：Standard Log Group retention 固定 7 天；`DeletionPolicy`／`UpdateReplacePolicy` 均為 `Delete`，stack cleanup 會刪除 log data。
- Sensitivity：30 天 retention、`Retain`、`CreateLogGroup`、wildcard stream、額外 IAM user 五項 mutation 均被測試抓到並已還原。
- R3 safety review：無 High／Critical blocker；principal-scope 缺口已補測。`AppRoleName`／`AppInstanceId` 關聯無法由此 stack 證明。
- Deployment gate：AWS batch 前須確認 instance profile→指定 AppRole、執行 CloudFormation validate、IAM Access Analyzer、允許精確 stream與拒絕其他 stream；stack delete 會失去此 demo log evidence。
- Local limitation：未安裝 `cfn-lint`；目前 schema gate 為 YAML parse 與精確 contract，不能取代 AWS validation。
- 官方依據：[AWS::Logs::LogGroup](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-logs-loggroup.html)、[CloudWatch Logs IAM resource scope](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/iam-identity-based-access-control-cwl.html)。
