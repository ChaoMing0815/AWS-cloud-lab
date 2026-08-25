# Tier 1 bounded AIOps Agent 驗證摘要

- Scope／risk／upstream source：R2；依 Tier 1 checkpoint 建立可部署至既有 EC2、讀取安全 application JSONL 並提出人工批准建議的最小 AIOps Agent。
- Architecture：`IncidentAnalyzer` 只建立 bounded sanitized facts；`BedrockIncidentAdvisor` 是可抽換 adapter，runtime entrypoint 固定讀取 `/var/log/co-story/application.jsonl`，不新增 CloudWatch read IAM 或常駐 AWS resource。
- Baseline：Backend `330 passed, 8 skipped`。
- Red commits：`bea8e08`（analyzer／adapter）、`8e6b7cb`（unhashable forged values）、`ac15c71`（EC2 entrypoint）、`f0d268f`（固定 runtime env 五鍵讀取）。
- Green commits：`ba9b553`、`069b939`、`a8d0bf3`。
- Input boundary：最多讀取最後 `200` 行，只接受 request／Storyteller exact allowlist schema；malformed、額外欄位、query path 與不合型別事件均丟棄，不把 request ID 或 raw line 傳給模型。
- Output boundary：固定五欄 JSON；action 只能為 `NO_ACTION`、`RUN_HEALTH_CHECK`、`RESTART_APPLICATION`、`CHECK_DATABASE`，且 `requires_human_approval` 必須為 `true`；Agent 本身沒有執行修復工具。
- Model boundary：單次 guarded Bedrock Converse，temperature `0`、max tokens `600`、retries `0`；沒有新增 Python dependency，沿用既有 exact model／Guardrail runtime configuration。
- Runtime boundary：SSM shell 不需 source 整份設定；entrypoint 只從固定 `/etc/co-story/runtime.env` 讀取五個必要 Bedrock key，忽略且不輸出其他設定。
- Targeted verification：incident analyzer／adapter／entrypoint `13 passed`；affected suite `58 passed`。
- Full regression：Backend `343 passed, 8 skipped`。
- Sensitivity：暫時移除 `requires_human_approval=true` guard 後，目標測試精確失敗；mutation 已還原，targeted 與 full regression 重新全綠。
- Release artifact：從 detached exact commit `59f54586324427e94760899531c0104722050204` 建立 `tier1-20260824-59f5458`；archive 約 `148 KiB`，SHA-256 `50331286421507ba7639a5f2ab5e4eb2c51ec0cbb7d92e2ef19d7db4b3946d60`，本機 `shasum -c` 為 `OK`，並確認 archive 含三個 AIOps module。build 使用暫時 worktree，未納入工作樹中未提交的簡報。
- AWS zero-model deployment gate（2026-08-25）：使用者將 exact archive／checksum 上傳至既有 private artifact prefix，並透過 SSM Session 執行兩次 exact-object S3 read；`co-story.tar.gz: OK`。第一次 installer member 檢查因 `tar | grep -q` 在 `pipefail` 下觸發 SIGPIPE false negative，於安裝前安全停止；修正只讀檢查後部署成功，active release 為 `tier1-20260824-59f5458`，application／CloudWatch Agent／public edge 均為 `active`。
- Zero-model runtime result：固定 safe log 最近 `200` 行全部通過 allowlist（accepted `200`、discarded `0`）；runtime 五鍵只驗證存在與 parser，不輸出值；AIOps entrypoint、report schema 與 `requires_human_approval=true` guard 通過。`bedrock_invocations=0`、deployment gate exit `0`。
- Residual risk：release 已部署，但尚未執行真實 Bedrock AIOps call、人工批准或受控 recovery action；exactly-one invocation 必須另行由使用者核准，輸出只作建議，不得自動 restart。
