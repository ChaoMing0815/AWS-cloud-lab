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
- 未建立Change Set、未替換instance、未傳送message或呼叫Bedrock。
