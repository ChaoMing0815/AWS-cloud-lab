# 缺件與交付風險清單

> **文件狀態：**本文件是 2026-09-07 的前置盤點歷史快照，已由 `README.md`、`written-report-manuscript.md` 與 `output` 目錄中的 DOCX 取代，不是目前待辦。下列「不製作 DOCX／PDF」、「不執行 merge」等敘述僅記錄當時的工作邊界，不得解讀為目前狀態或後續限制。

## 當時待補齊或由整合 task 決定的項目（歷史）

- 尚未逐檔建立「主張 → 證據 → 限制」的完整索引；本輪只完成 routing。
- 需確認最終 canonical evidence 是否已涵蓋 CloudFormation template、Change Set 與各 production release 的 exact source 關聯；不得以舊 SHA 或候選 PPTX 代替。
- 需逐張完成 screenshots public-safety audit；inventory 只能證明文字已去識別化，不能自動證明圖片安全。
- 需補齊兩台 Worker replacement-safe bootstrap／self-healing 的限制說明；現有證據明確保留此 residual risk。
- 需整理 CloudWatch／AIOps 的 synthetic incident 與「建議而非自動執行」證據，避免誇大 outage recovery。
- 需把 strict TDD 的 Red／Green、negative／sensitivity、測試效益整理成跨冊索引，而非重複貼完整 log。

## 當時確認未部署的範圍（歷史）

Route 53、CloudFront/CDN、ELB/ASG、SNS、App Runner、API Gateway、Lambda、SageMaker、DynamoDB、Step Functions、Bedrock Knowledge Bases／RAG。它們只能放在第六冊獨立「概念延伸／未部署」學習報告，並說明未採用原因與若未來啟動所需新核准。

## 當時的交付前安全限制（歷史）

- 不製作 DOCX／PDF 成品於本輪。
- 不修改 README、CURRENT、checkpoints、task list、deployment log、程式、治理檔、AWS／workflow／infra／ops。
- 不執行 AWS CLI、SSM、S3、Bedrock、deploy、push、PR 或 merge。
- 產出前執行 `scripts/check_branch_boundaries.py --base a4870cbe7f3371badee0e6b155d1fcd5ed511372` 與 `git diff --check`；若 branch／Git metadata 權限仍阻擋，須在交付摘要明示。
