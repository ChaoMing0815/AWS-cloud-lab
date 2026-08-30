# Tier 2 Storyteller schema 安全診斷驗證摘要

- Scope／risk／upstream：R2；針對 AWS exactly-one 回報 `SCHEMA_INVALID` 但缺乏安全子分類的阻塞點。
- 行為邊界：保留既有 `SCHEMA_INVALID`、retry、SQS ack 與結果狀態，只增加固定 allowlist 診斷碼。
- 隱私邊界：不保存或輸出 Bedrock 原始 response、tool input、prompt、ARN、secret 或玩家內容。
- Baseline：Bedrock adapter、StoryResolution worker 與 safe logger 共 72 項通過。
- Red commits：`d06f051`、`5df2658`、`6d44121`。
- Green commit：`e1eb544`。
- Targeted verification：22 項 schema 分類、worker retry contract 與 logger allowlist 測試通過。
- Affected verification：Bedrock、workflow、safe logging、Tier 2 production／async worker 共 118 項通過。
- Full regression：Backend 791 項完整 suite 通過；僅既有 Starlette `httpx` deprecation warning。
- Negative：非 allowlist 診斷與非 `SCHEMA_INVALID` 診斷均 fail closed；夾帶額外原始欄位的事件不落檔。
- Sensitivity：暫時允許 `raw model response` 時負面測試如預期失敗；還原後目標測試重新通過。
- Integration：PR #58四項CI全綠，merge commit `81bf54af63684681ccc8bf8b22c6c96503ae9b47`。Worker artifact run `33296013600`通過production approval、ARM64 immutable push、exact-digest Trivy與manifest，digest為`sha256:2d5d5866f54879e79882644f4b45af2475650ddc9972e6b91cfe786886cddfbc`。
- Worker rollout：使用者透過bounded SSM選取兩台private Worker，兩台皆回preflight safe、service active、container running、restart `0`、mode async與credential absent；Web／publisher image與Web `sync`均未改變。
- AWS exactly-one：新marker只建立一個job，`retry_seed=2`限制最多一次Bedrock invocation；publisher stop／start通過、dispatch attempts為`1`、final attempt為`3`、result為`applied`、Room回`COLLECTING_ACTIONS`，且沒有自動重跑。
- Cleanup／postflight：成功狀態與result fingerprint／room version驗證後才精確刪除marker；`marker_count=0`、publisher active、Web `sync`，主Queue／DLQ available與in-flight四項皆為`0`。
- Rollback／residual risk：previous Worker digest仍為可回復資產；safe diagnostics未在成功路徑輸出事件。此證據不授權或證明玩家可見async activation、多人polling或rollback。
