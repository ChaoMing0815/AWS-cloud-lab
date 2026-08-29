# Tier 2 SQS Worker runtime validation

- 日期：2026-08-29
- Base：`origin/main` exact `391c4d6151f1743fab6aab22f14755aa6ee5e12d`
- Branch：`codex/tier2-sqs-worker-runtime`
- 風險：R2 runtime整合；secret／IAM使用邊界以R3 negative與sensitivity驗證
- AWS寫入：無；未執行AWS CLI、S3讀取或Bedrock呼叫

## 完成範圍

- SQS message只接受`schema_version=1`與opaque `job_id`，單次最多接收一筆。
- 20秒long poll、180秒visibility、60秒heartbeat；只有處理成功且heartbeat停止後才刪除receipt。
- Retryable pending、處理例外、heartbeat失敗與invalid payload均不ack；既有SQS redrive負責最終DLQ。
- Production Worker在建立AWS clients前驗證exact queue URL與設定，SDK retry設為0，不與job retry／redrive疊加。
- Runtime secret只接受精確ARN、同Region RDS endpoint、regular non-symlink CA及`co_story_app`的exact兩欄JSON；`verify-full` DSN只存在程序記憶體，錯誤輸出固定且不含provider／secret內容。
- Worker systemd unit封裝於既有image，使用non-root、read-only rootfs、no-new-privileges、無published port、無HTTP healthcheck、CloudWatch awslogs與Worker-only `async` entrypoint；Web unit仍為`sync`。

## TDD與驗證

- SQS transport／heartbeat／runner：先以missing adapter與missing heartbeat建立Red，再完成Green；invalid／expanded payload、retry、處理例外及heartbeat failure皆為negative gate。
- Production composition／secret bootstrap／Worker unit：各自先建立missing-behavior Red；Worker unit另以五類mutation sensitivity驗證writable root、published port、host secret file、Web command及sync mode會被拒絕。
- 完整regression第一次發現bootstrap結束後殘留`DATABASE_URL`，造成後續Web tests誤選PostgreSQL composition；新增代表性Red後以`finally`恢復原環境，受影響51項測試與第二次完整regression均通過。
- 新增核心targeted：`39 passed`。
- 受影響runtime／container suites：`104 passed`與`76 passed`。
- Backend collection：`731 tests collected`。
- Backend完整regression：`715 passed, 16 skipped, 1 existing Starlette deprecation warning`。
- Local image build：成功，新增unit已複製至`/usr/local/share/co-story/co-story-worker-container.service`並設為`0444`。
- Frontend：本機環境無Node／npm；由既有GitHub CI merge gate執行，不在本文件假稱本機通過。
- `git diff --check`：通過。

## 明確未做

- 未部署或啟動Worker container。
- 未傳送production SQS message、未呼叫Bedrock、未讀取secret value。
- 未修改20-resource foundation、IAM、成本或Web active release。
- 未將Web從`sync`切換為`async`。
- Producer publisher／reconciliation、DLQ operator flow與AWS E2E仍需獨立批次。
