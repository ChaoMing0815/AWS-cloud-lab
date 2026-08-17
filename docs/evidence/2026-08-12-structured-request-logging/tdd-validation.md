# Structured request logging 驗證摘要

- 範圍／風險：R2；API request event 的 allowlist logging 與敏感資料去除。
- Baseline：Backend `235 passed, 8 skipped`。
- Red：`34ab77c test(red): specify structured request logging`；缺 request ID 與結構化 event，兩項目標 assertion 預期失敗。
- Green：`a0659cb feat(green): add redacted request logs`；每個 request 產生 server-side ID，僅記錄 `request_id`、method、path、status、latency_ms。
- Targeted：structured logging＋internet release gates，11 passed。
- Full regression：Backend `237 passed, 8 skipped`。
- Sensitivity：將 path 改為完整 URL 後，query token 進入 log，測試預期失敗；已還原為純 path。
- Residual risk：此切片只記 request summary；CloudWatch transport、retention 與 runtime log format 在 AWS change batch 驗證。
