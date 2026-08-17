# Tier 0 Bedrock bounded runtime IAM 驗證摘要

- Scope／risk：Batch 5A；R3 IAM。只修改既有 `AWSFinalProjectAppRole` 的 inline policy，不新增 AWS resource。
- Upstream：已核准 Batch 5A envelope、`tier0-aws-change-envelope.md`、IAM boundaries 與 AWS Bedrock 官方權限文件。
- Baseline：Backend regression 全綠；工作樹位於 `codex/tier0-bedrock-guardrail`。
- Red：`525a79b`；缺少固定 model／Guardrail parameters 與 bounded policy 時，targeted tests 為 `2 failed, 5 passed`。
- Green：`a505e92`；新增固定 Nova Lite、數字 Guardrail version、exact resource 與 APAC profile policy。
- Safety review Red／Green：`c7a5f38`／`f63c488`；將過寬的任意數字 version 收斂為只允許 `1`。
- Targeted verification：`backend/tests/test_tier0_compute_template.py`，`7 passed`。
- Full regression：Backend `292 passed, 8 skipped`；無新增 skip。
- Negative boundary：不授予串流、其他 model、DRAFT、其他 Guardrail、IAM 管理或服務級 Full Access。
- Sensitivity：model ARN 改成 wildcard、Deny condition 反轉、移除任一 APAC destination，三者皆被 targeted test 攔截；mutation 已還原。
- AWS validation：尚未執行；待 Console 建立並檢查 change set、Access Analyzer 與正負 IAM simulation。
- Rollback：CloudFormation 移除 inline policy；已發布版本停止使用，任何版本刪除另行核准。
- Residual risk：Guardrail version `1` 尚未發布，template 尚未部署，尚未執行真實 Bedrock invocation。
