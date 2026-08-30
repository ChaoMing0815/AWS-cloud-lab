# Tier 2 Worker Guardrail profile IAM 驗證

- Scope／risk／upstream source：R3 IAM；修正Tier 2 Worker呼叫既有APAC cross-Region Guardrail時的`AUTHORIZATION_ERROR`。使用者只核准擴充`bedrock:ApplyGuardrail`的精確resources，不新增action、wildcard、model、Guardrail或AWS resource。
- AWS failure evidence：exactly-one job只dispatch一次並以attempt `3/3`完成，result為`AUTHORIZATION_ERROR`；marker已清除，主Queue／DLQ available與in-flight皆為`0`，publisher active、Web `sync`。
- Root cause：Tier 0已驗證AppRole允許Guardrail ARN及Tokyo對應的六個`apac.guardrail.v1:0` destination-region ARNs；Tier 2 WorkerRole只允許Guardrail ARN。AWS官方文件要求cross-Region Guardrail caller同時具備所有destination profile resources的`ApplyGuardrail`權限。
- Baseline：`backend/tests/test_tier2_worker_infrastructure.py`為`9 passed`。
- Red commit：`887ed72`；新增精確七項resource contract，因template仍只有單一Guardrail ARN而失敗。
- Green commit：`dfe3956`；只把`ApplyExactGuardrail.Resource`改為既有Guardrail ARN加六個APAC profile ARN，action仍精確為`bedrock:ApplyGuardrail`。
- Targeted verification：新contract通過；Tier 2 Worker infrastructure suite `10 passed`。
- Full regression：完整Backend suite final exit `0`；既有Starlette／httpx deprecation warning不影響結果。
- Negative／boundary：contract精確比對六個Tokyo destination Regions並拒絕`Resource: "*"`；未修改`InvokeModel` allow／deny、SQS、ECR、Secret、Logs、permissions boundary或20-resource inventory。
- Sensitivity：暫時把`ap-northeast-1`變異為`ap-east-1`後targeted test失敗；還原後重新通過，mutation未commit。
- Rollback／residual risk：回復Green commit即可還原repo變更。Production WorkerRole尚未更新；必須先經PR CI，再以只修改WorkerRole inline policy的CloudFormation Change Set獨立核准，之後新的Bedrock invocation仍須另一份exactly-one核准。
