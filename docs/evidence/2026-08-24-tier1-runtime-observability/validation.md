# Tier 1 Batch 11B runtime observability 執行摘要

- 核准邊界：使用者核准 Batch 11B；由使用者透過 AWS Console／SSM 操作，未由 Agent 執行 AWS CLI、S3 讀取或 Bedrock 呼叫。
- CloudWatch Agent 安裝：SSM Distributor `AWS-ConfigureAWSPackage` 執行成功，單一 target、`0` error；實機 package 為 `amazon-cloudwatch-agent-1.300071.0b1720-1.aarch64`，control tool 與 repo config 均存在。
- 安裝後 preflight：`co-story.service=active`、安全 JSONL runtime path 尚不存在、CloudWatch Agent service 為 inactive，符合尚未啟用 collection 的預期狀態。
- 首次設定嘗試：腳本加入安全 JSONL runtime 設定並重啟 application 後，立即檢查 loopback `127.0.0.1:8000` 時得到 `curl (7) Could not connect`；腳本依停止條件執行 rollback，回報 `rollback=attempted`、`configure_result=7`。
- 首次停止點：失敗發生在 CloudWatch Agent 啟動與 CloudWatch log delivery 驗證之前，因此當時未宣稱安全 log stream、metric filter 或 runtime alarm path 已通過。
- Rollback audit：單次唯讀 SSM Session 確認 `co-story.service=active`、runtime env 已移除 `CO_STORY_APPLICATION_LOG_PATH`、`application.jsonl=absent`、CloudWatch Agent service 仍為 `inactive`；不需讀取 service failure journal，production 已恢復且沒有啟用 log collection。
- Health document 修正與部署：依 R3 嚴格 TDD 將固定路徑修正為 `/api/v1/live`、`/api/v1/ready`；Red `dcd8efd`、Green `529d223`，targeted `5 passed`、Tier 1 affected `15 passed`、Backend `330 passed, 8 skipped`，代表性舊 `/live` mutation 會被測試攔截。使用者透過 Console 執行唯一 `HealthCheckDocument Modify` 的 Change Set，operations stack 回到 `UPDATE_COMPLETE`；Document version `2` 同時為 latest／default。
- Health document runtime gate：首次 Run Command 僅 target 單一 app instance，`CheckCoStoryHealth=Success`、response code `0`、error empty；輸出精確為 `service=active`、`live=200`、`ready=200`。未使用 S3／CloudWatch output，未重試或執行其他 Document。
- Runtime retry：單一 SSM Session 命令加入安全 JSONL env、restart application，並以 60 秒 bounded wait 輪詢 `/api/v1/ready`；第一次 curl 在 restart 空窗回 `7`，後續於期限內成功。最終 `application=active_ready`、runtime log setting present、JSONL present 且 `co-story:co-story:640`、CloudWatch Agent active，沒有執行 rollback。
- CloudWatch delivery gate：Tokyo Console 的固定 `/co-story/tier1/application` Log Group 已出現 instance stream 與最新事件；代表性事件為 `GET /api/v1/ready`、status `200`、latency `101 ms`。JSON 只含去識別化 `request_id`、method、path、status、latency，未見 query、prompt、cookie、authorization、database URL 或其他 secret；未產生額外請求或 5xx。
- IAM runtime 負向 gate：由使用者在 SSM Session 以 EC2 AppRole 對既有 Log Group 的未核准 stream `iam-negative-control-never-create` 嘗試單次 `PutLogEvents`；application 與 Agent preflight 均為 active，API 回 `AccessDenied`，腳本回報 `negative_write=denied_expected`、exit `0`。未建立越界 stream、未修改 IAM，也未輸出 credential 或 runtime secret。
- 5xx Alarm trigger／recover gate：在確認 Alarm 為 `OK`、Actions 為 `No actions` 後，由使用者在 SSM Session 對既有安全 JSONL append exactly one allowlist synthetic request event，status `500`、path `/tier1/incident-simulation`、request ID `tier1-alarm-00e00384f5c247769f77b15c16765e20`；寫入前後 application 與 Agent 均為 active，未呼叫 application API、S3 或 Bedrock。Alarm `co-story-tier1-application-5xx` 於本地時間 `2026-08-24 22:23:03` 轉為 `In alarm`，條件顯示 `Application5xx >= 1 for 1 datapoints within 1 minute`，Actions 維持 `No actions`。未注入第二筆事件、未修改 Alarm；狀態於 `22:29:03` 自動回到 `OK`，完成 trigger／recover gate。
- 成本：既有 EC2 上的 Agent 已開始少量 CloudWatch Logs ingestion；Log Group 仍為 7 天 retention，未新增資源。正向 delivery、代表性越界寫入拒絕與單筆 5xx Alarm trigger／recover 均已通過。

結果：**PASS／RUNTIME OBSERVABILITY INCIDENT PATH**。Health Document、bounded restart、安全 JSONL、Agent、固定 Log Group 正向 delivery、代表性 IAM 越界拒絕，以及 exactly-one 5xx Alarm trigger／automatic recover 均通過；後續進入 AIOps incident analysis，且不重複注入 5xx。
