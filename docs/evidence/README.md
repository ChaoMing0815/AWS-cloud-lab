# 驗證證據索引與保留規則

本目錄保存能支持課程驗收、安全聲明與高風險變更的精簡證據。它不是原始 terminal log、每日工作紀錄或每次測試輸出的集中地。依 [ADR-0008](../decisions/0008-fix-final-delivery-scope.md)，索引重點是已實作的 production 組件化、自動部署與 bounded Support Agent；Tier 4／5 future roadmap 不需要補證據。

## 保留原則

應保存：

- AWS milestone 的實際部署與驗收結果。
- IAM、secret、migration、session、成本與 rollback 等 R3 邊界。
- 重要 R2／R3 功能的 Red／Green、負面測試與 sensitivity 摘要。
- 最終 Demo、三玩家 E2E、資料 persistence 與 incident recovery 證據。

不另建 evidence：

- 一般 R1 refactor、格式化或局部 bug fix。
- 可由 CI／tests 與 Git commit 直接重現的完整 console output。
- 每日工作清單、討論過程或已被取代的中間方案。
- 重複記載於 `CURRENT`、deployment log 與 checkpoint 的同一狀態。

## 公開安全規則

- 只保存去識別化文字與必要截圖。
- 不保存 account ID、完整 ARN、public／private IP、RDS endpoint、instance／subnet／Security Group ID、bucket 隨機 suffix、Email、cookie、token、DSN 或 secret value。
- 原始截圖若含上述資訊，先在本機遮罩；TemporaryItems 中的檔案不算正式 evidence。
- 不保存 `~/.aws`、credential、Keychain、Access Key 或可重建登入狀態的內容。
- 證據若無法安全去識別化，改用文字記錄驗證項目與結果。

## AWS milestone

- [帳號與成本 Console inventory](2026-08-13-tier0-batch0-console-inventory/inventory-summary.md)
- [IAM bootstrap 與 Tier 0 network deployment](2026-08-14-tier0-network-deployment/validation.md)
- [Private RDS IaC 與 deployment](2026-08-14-tier0-rds-iac/tdd-validation.md)
- [EC2＋SSM management plane](2026-08-15-tier0-compute-iac/tdd-validation.md)
- [Bedrock Guardrail baseline](2026-08-15-tier0-bedrock-guardrail/validation.md)
- [Artifacts、runtime secrets、migration 與 internal staging](2026-08-16-tier0-internal-staging/validation.md)
- [Batch 9A、Prompt Attack 未歸因結果與公開試玩 readiness](2026-08-19-tier0-public-trial-readiness/validation.md)
- [Tier 1 CloudWatch／AIOps／SSM 完成驗證](2026-08-25-tier1-completion/validation.md)
- [Tier 2 production async activation 與最終 runtime 狀態](2026-08-31-tier2-web-async-activation/validation.md)
- [Tier 2 玩家 UI release](2026-08-31-tier2-web-ui-release/validation.md)
- [Tier 3 production release](2026-08-31-tier3-production-release/validation.md)
- [Support Agent production 整合](2026-08-31-support-agent-integration/validation.md)
- [Support Agent CSP corrective](2026-08-31-support-csp-corrective/validation.md)

## 產品與 release gates

- [三玩家 Browser E2E](2026-08-10-three-player-browser-e2e/validation.md)
- [PostgreSQL persistence](2026-08-10-postgres-persistence/tdd-validation.md)
- [LLM failure recovery](2026-08-10-llm-recovery/tdd-validation.md)
- [Bedrock production composition](2026-08-11-world-generation-bedrock/tdd-validation.md)
- [Local production parity gate](2026-08-13-production-parity-local-gate/validation.md)

其餘日期目錄屬 feature-level 歷史證據，可由 Git history 或本目錄直接查閱，不在根 README 逐項列出。
