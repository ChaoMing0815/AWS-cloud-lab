# Tier 2 Worker runtime deployment validation

- 日期：2026-08-29
- Source main：`0ea4b125ad87afac76ff72e67e0f63dd9299d509`
- Artifact workflow：`33233803509`
- Worker image digest：`sha256:ede0f8e571824e2b1100a537795825ecdff415b0dbd1fcbc1e8a1ebd50bf1757`
- 操作者：使用者透過GitHub production approval與AWS Systems Manager Console；Agent未執行AWS CLI、S3讀取或Bedrock呼叫

## Artifact gate

- PR #39四項CI全綠後合併main。
- Worker-only workflow通過production人工approval、ARM64 immutable build／ECR push、exact-digest Trivy `CRITICAL,HIGH` fail-closed scan及manifest artifact。
- Workflow不含SSM或Web release call；active Web image與`sync` mode未變。

## Deployment與idle gate

- 使用者以同一bounded SSM Run Command手動選取兩台private Worker，安裝精確digest、root-only runtime metadata、RDS CA與hardened systemd unit。
- SSM targets精確`2/2 Success`，兩台response code皆為`0`，最後輸出皆為`worker_release=verified`與同一digest。
- CloudWatch Log Group `/co-story/tier2/worker`出現兩個不同instance log streams。
- 主Queue與DLQ的available messages及messages in flight皆為`0`。
- 未傳送production或synthetic message、未觸發Bedrock、未建立StoryJob結果，也未啟用Web producer／async。

## 成本與資源邊界

- CloudFormation仍為既有20-resource foundation；未新增或修改IAM、network、compute、Queue、alarm或第二個NAT。
- 增量僅為既有ECR lifecycle內的一個image、SQS idle long-poll requests與空log streams；不假造即時價格，仍受USD 35上限與2026-09-08清理日約束。

## Residual risk／rollback

- 目前runtime以SSM安裝在現有兩台instance；ASG replacement的新instance只有Docker foundation，不會自動重建Worker service。完成replacement-safe bootstrap前不得宣稱self-healing Worker runtime。
- Producer尚未啟用且Queue為空；若需回復本次第一版部署，停止並disable `co-story-worker.service`、移除`co-story-worker` container與Worker專用unit／env／CA即可回到foundation-only狀態，不影響Web。
- 原始截圖位於TemporaryItems，未直接入庫；本文件只保存去識別化的狀態摘要。
