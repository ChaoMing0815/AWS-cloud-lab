# Tier 1 Batch 11A 基礎可觀測性與受限 SSM 文件部署摘要

- Scope／principal／Region：使用者以 MFA IAM user 在 Tokyo `ap-northeast-1` 操作 AWS Console；Agent 未執行 AWS CLI。
- Cost preflight：Budget alert 正常、credits `US$131.84`、當月成本 `US$8.16`；既有 EC2 running、AppRole 對應、SSM managed node online。
- Observability Change Set：`CREATE_COMPLETE／AVAILABLE`，精確四筆 `Add`；change set ID 已於使用者截圖遮蔽。
- Observability resources：`ApplicationLogGroup`、`Application5xxMetricFilter`、`Application5xxAlarm`、`ApplicationLogWritePolicy` 均由使用者回報 `CREATE_COMPLETE`。
- Alarm initial state：`OK`；尚未安裝 Agent 或送入 application log，因此未執行觸發測試。
- Operations Change Set：`CREATE_COMPLETE／AVAILABLE`，精確一筆 `HealthCheckDocument Add / AWS::SSM::Document`，無 IAM、Association、排程或其他資源。
- Operations resource：使用者回報 `HealthCheckDocument=CREATE_COMPLETE`；尚未執行 Run Command。
- Safety：兩份 Change Set 均為 rollback-all；沒有 EC2、RDS、SNS、Lambda、Bedrock、NAT 或自動修復變更。
- IAM boundary：部署的是已通過 R3 contract 的 single-instance log-stream policy；AWS Access Analyzer／實際正負權限測試仍待後續 gate。
- Cost surface：7 天 Standard Log Group、單一 custom metric 與單一 Alarm；SSM Document 無 Association／排程。實際新增費用尚待帳務延遲後確認。
- Rollback：刪除 `co-story-tier1-observability` 與 `co-story-tier1-operations`；observability stack delete 會刪除 Tier 1 demo log data。
- Evidence limitation：使用者提供兩張已遮蔽 change set ID 的 Console 圖；原圖位於 repo 外，未直接 commit。兩次回報的 `stack_status` 欄位留空，但精確資源均回報 `CREATE_COMPLETE`。
- Result：Batch 11A 資源層級 PASS with follow-up validations；在 Agent install、log delivery、IAM negative test 與實機 SSM health check 前不宣稱 Tier 1 runtime gate 完成。
