# Tier 1 完成驗證

## 結果

**PASS／TIER 1 COMPLETE**。CloudWatch application／sanitized system logs、HTTP／LLM／system metrics、Dashboard、disabled-actions Alarm、Session Manager、Run Command、bounded AIOps 與人工批准 incident response 均已在 AWS 實機留下證據。這個結論不宣稱已完成實際 outage restart recovery，也不把 synthetic zero baseline 說成真實 retry／fallback incident。

## Repo-local TDD 與 regression

- Red `9ac925c` 定義 system telemetry、HTTP／Storyteller metrics、Dashboard 與最小 IAM completion gate；Green `a9420c0` 完成實作。
- Change Set 第一版顯示 `ApplicationLogWritePolicy Replacement=True／ReplaceAndDelete`，依停止條件未執行。根因為 named `AWS::IAM::ManagedPolicy.Description` 變更；Red／Green 修正 `dd553b1` 保留既有 Description，使第二版為 `Modify／Replacement=False`。截圖：[無替換 Change Set](change-set-no-replacement.png)。
- `mem_used_percent` 首次缺失；依 AWS Agent `drop_original_metrics` 語意，以 Red／Green `4a51e0e` 保留唯一 InstanceId memory series，disk 仍保留 aggregation 去重。
- Full Backend gate：`358 passed, 8 skipped`；Frontend：`94 passed`。completion affected suite：`89 passed`；memory 修正 affected suite：`16 passed`。

## AWS 更新與安全邊界

- `co-story-tier1-observability` 第二版 Change Set 共 `9` 項：`8 Add`，以及 `ApplicationLogWritePolicy Modify／Replacement=False`；Stack 最終 `UPDATE_COMPLETE`。
- 新增 `/co-story/tier1/system`，retention `7` 天；只收固定 `/var/log/co-story/system.jsonl`。每五分鐘事件只包含 application、CloudWatch Agent、public edge 三個 allowlist state，不收 raw journal、auth、Nginx、query、cookie、prompt 或 secret。
- AppRole 只增加固定 system stream 寫入，以及 `cloudwatch:PutMetricData`；後者雖須 `Resource: "*"`，仍以 `cloudwatch:namespace=CoStory/Tier1/System` 限制。既有越界 Logs stream 負向測試仍為 `AccessDenied`。
- CloudWatch Agent validation 兩階段均成功；application、Agent、public edge、system-health timer 持續 active。system JSONL 為 `root:co-story:640`，application JSONL 為 `co-story:co-story:640`。
- Active release：`tier1-20260825-4a51e0e`；archive `154474` bytes，SHA-256 `371cf50353ff4d54d557b6acbd22d659d09d5a6536e03e515ab31fe3f0704e8a`，EC2 checksum `OK`。

## CloudWatch 實機證據

- System log delivery：`2026-08-25T22:55:52.448+08:00` 收到 `{"event_type":"system_health","application":"active","cloudwatch_agent":"active","public_edge":"active"}`。
- `CoStory/Tier1/System` 同一 InstanceId 同時存在 `mem_used_percent` 與 `disk_used_percent`：[metric 清單](system-metrics.png)、[Dashboard](system-dashboard.png)。
- 一次經使用者核准的正常 Nova Lite 世界草稿生成成功；未重試。Dashboard 顯示 input `206`、output `465`、LLM latency p95 `2,823 ms`、估計成本 `US$0.00012396`：[數值](storyteller-metrics-values.png)。
- exactly-one synthetic recovery zero baseline 為 `retry_count=0／fallback_count=0`；marker `completed_exit=0`、exact match `1`，Bedrock invocations `0`、recovery actions `0`。Dashboard 顯示兩者均 `0`：[圖表](recovery-zero-baseline.png)、[tooltip](recovery-zero-values.png)。此事件只驗證 metric pipeline，不代表發生真實 retry／fallback。
- HTTP latency 與既有 5xx metric 同時出現在 Dashboard；exactly-one 500 Alarm 已有獨立 `OK → In alarm → OK` 證據，Actions 全程 `No actions`。

## AIOps／SSM 完成證據

- Session Manager 可連線且 EC2 無 public SSH；維運不依賴 SSH。
- `CoStoryHealthCheck` version `2`／default 使用 `/api/v1/live`、`/api/v1/ready`，單一 target Run Command 為 `Success`、response `0`，輸出 service active、live `200`、ready `200`。
- Forced-tool Nova Lite report 具固定 schema 與 `requires_human_approval=true`。健康狀態建議 `NO_ACTION`；synthetic 500 建議缺乏 DB 證據的 `CHECK_DATABASE` 時，使用者拒絕並改批准較安全的 `RUN_HEALTH_CHECK`，完成偵測→判讀→人工批准→受控處置。

## 操作經驗與後續規則

- 一次互動式 SSM 指令因 protected application log 讀取漏用 `sudo`，preflight 得到空值後執行頂層 `exit`，導致 Session 被終止；production services 未受影響。
- 後續互動式 Session 指令禁止頂層 `exit`；gate 失敗只輸出 `stopped` 並保留 prompt。需要 exit code 的流程放在 subshell；protected file 唯讀檢查明確使用 `sudo`。

## 成本與殘餘風險

- 共 `9` 條 custom metric series、`1` 個 custom dashboard、`1` 個 standard alarm metric，以及兩個 `7` 天 log groups；若帳號其他使用量未占用額度，仍在 CloudWatch Free Tier 公開額度內。實際帳單仍以 Billing Console 為準。
- Storyteller retry／fallback 目前只有 zero baseline；真實 retry／fallback 仍由既有 deterministic recovery tests 與未來 incident 證據補充。
- AIOps incident 是 synthetic 500 且 application 未中斷；受控修復選擇為唯讀 health check，不宣稱已證明 outage restart recovery。
