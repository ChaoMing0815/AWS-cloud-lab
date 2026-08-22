# Tier 1 Application 5xx Metric／Alarm 驗證摘要

- Scope／risk／upstream：R3 observability cost／cleanup；依 Tier 1 gap analysis 完成 repo-local MetricFilter／Alarm contract，未 deploy。
- Baseline：Backend `323 passed, 8 skipped`，工作樹乾淨。
- Red：`cc208d4` 定義單一 JSON 5xx metric 與 1/1 minute alarm；`aad2626` 收斂為 500–599 並禁止 template `Transform`。
- Green：`fc96f12`；template 新增一個 `AWS::Logs::MetricFilter` 與一個 `AWS::CloudWatch::Alarm`。
- Targeted／affected：`14 passed`（Tier 1 IaC、Agent contract、安全 file sink 與 structured request logging）。
- Full regression：Backend `325 passed, 8 skipped`。
- Input boundary：filter 僅接受 `{ ($.status >= 500) && ($.status <= 599) }`；request-only 語意依賴上游安全 sink 只允許 request schema 帶 `status`。
- Cost boundary：只有 `CoStory/Tier1`／`Application5xx` 單一 custom metric；`DefaultValue: 0`、無 dimensions，避免 request ID 等高基數成本。
- Alarm boundary：`Sum`／60 秒／1 of 1／threshold 1／`notBreaching`；`ActionsEnabled: false` 且沒有 Alarm／OK／InsufficientData actions。
- Sensitivity：600+、request ID dimension、300 秒 period、SNS action、`Retain` 與 `Transform` 六項 mutation 均被測試抓到並已還原。
- R3 safety review：無 High／Critical；500–599 Medium 語意缺口及 Transform hardening 已修正。
- Rollback／residual：MetricFilter／Alarm 均為 `Delete`；若部署時停用 rollback 或選擇保留成功資源，模板無法強制清理。
- 官方依據：[MetricFilter](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-logs-metricfilter.html)、[JSON filter syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html)、[CloudWatch Alarm](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-cloudwatch-alarm.html)。
