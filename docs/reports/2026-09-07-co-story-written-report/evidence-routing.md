# 章節 evidence routing

| 冊次 | 首要證據 | 輔助證據 | 寫作提醒 |
|---|---|---|---|
| 第一冊 | `docs/product/source-of-truth.md`、`docs/decisions/0008-fix-final-delivery-scope.md` | `docs/governance/approval-log.md`、`docs/testing-strategy.md` | Tier 0–5 只作課程對映背景，不作章節或完成標準 |
| 第二冊 | Tier 0 network／RDS／compute validation | CloudFormation template 與對應 screenshots | 以 flow：template → Change Set → Console 驗證 → rollback |
| 第三冊 | Bedrock smoke／composition、public trial、production release validation | MVP Spec、story quality validation | Nova Lite 是 bounded storyteller；Support Widget 不是 RAG |
| 第四冊 | tier2 publisher、worker runtime、async activation validation | tier2 migration／producer／result validation | 明寫 queue empty／idle gate 與 replacement-safe residual risk |
| 第五冊 | tier1 completion、tier3 control plane／delivery／production release | SSM health check、deployment efficiency、Trivy evidence | 人工 approval 與 fail-closed gate 是設計，不是自動化缺陷 |
| 第六冊 | Support Agent／Widget integration validation | branch-boundary validation、rules retrieval validation | 只寫 cited／unsupported／local draft；概念延伸另節列出未部署服務 |

每個正文主張至少附：證據日期、相對路徑、驗證結果、限制／殘餘風險。截圖只作已完成 sanitized review 後的輔助證據。
