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
- Rollback／residual risk：可回退 Green commit；需另行核准 image build、Worker deploy 與新 exactly-one invocation 才能取得真實分類。
