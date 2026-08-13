# CURRENT：目前工作交接

- 更新日期：2026-08-13
- Branch：`codex/session-lifecycle`
- 最後全綠功能基準：`fafea8a`（WorldDraft 確認契約與欄位錯誤提示）
- Regression：Backend `239 passed, 8 skipped`；Frontend `80 passed`（使用工作區 bundled Node runner）
- AWS：專題 workload 為 0；本批無 AWS 寫入

## Current

- 本機 MVP P0 release gate 已全綠：正式入口、三玩家回合、結局、PostgreSQL restart、LLM recovery、polling 與 session lifecycle。
- Transfer code 為 10 分鐘一次性 hash-only；redeem 原子 rotate Player session／CSRF 並撤銷舊 session。
- 房主轉移自己的 Player 時保留原 Host session；完成房在保留期可唯讀轉移。
- 房主永久刪除有原子 repository contract、204 與三 cookie 清除；刪後所有舊 session／transfer 不可用。
- Browser 已觀察 offline→reconnected、session-expired、completed 與 console 無未處理錯誤。
- 房主可輸入 3–5 個關鍵字生成兩次可編輯 WorldDraft；失敗與 replay 仍受 inference／idempotency 成本邊界限制。
- `BedrockStoryteller` 已完成 Converse、Guardrail、schema、canonical 結果 prompt 與安全錯誤分類；production 缺 Region／model／Guardrail／token ceiling 時拒絕啟動。
- Migration 為獨立、可重跑 command；readiness 同時驗證 PostgreSQL 與所有 schema migration version，Web boot 不會自動套用 migration。
- 到期房間 cleanup 以獨立 use case／repository bulk delete 實作：所有狀態的 `expires_at <= now` 均會刪除，demo `None` 與未到期房間保留；未連接 timer 或 Web boot。
- `requirements-prod.txt` 為精確 runtime lock，包含 `boto3`／`botocore`；開發依賴引用同一 lock。
- runtime bundle 採 Nginx loopback proxy、systemd non-root single worker 與 repo 外 environment／TLS；release 以 per-release `.venv`、candidate readiness 與 `mv -Tf` 原子切換，rollback 禁止 schema downgrade。
- API request log 為 JSON allowlist：僅含 server-generated request ID、method、純 path、status 與 latency；不得記錄 query、headers、cookies 或 body。
- 正式 `/rules` 提供唯讀的新手規則摘要，首頁與遊戲頁可開啟；不改變遊戲規則、session 或 API state。
- 預設 Mock 生成的 WorldDraft 可直接確認為 Lobby，不再因 `premise` 長度不足得到 `422`；HTTP 的 FastAPI `422` 會以安全的欄位級提示標示世界表單，草稿保持可編輯。
- 本機 MVP 為 **100%（AWS 串接準備完成）**：乾淨 production lock install／import、production live／ready fail-closed、security headers、release assets 與 tracked-file secret scan 已驗證；完整定義與停止規則見 `docs/qa/local-mvp-test-plan.md`。

## Next

```text
IaC Red（僅 repo-local contract，不建立 AWS 資源）
→ Tier 0 AWS bounded change envelope 人工核准後才可操作 AWS
```

本機 MVP 100% 不等於 Tier 0 AWS 已完成：真實 model／Guardrail、RDS readiness、TLS 與 AWS 驗證尚未執行。Residual risk：idempotency 仍是 process memory，不宣稱 multi-process exactly-once；release assets 尚未在 Linux VM／EC2 實機驗證。
