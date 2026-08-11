# CURRENT：目前工作交接

- 更新日期：2026-08-11
- Branch：`codex/session-lifecycle`
- 最後全綠功能基準：`71650a2`（世界生成／Bedrock milestone）
- 暫停中的 Red checkpoint：`7edc7cf`（migration-aware readiness；尚未 Green）
- Regression：Backend `212 passed, 8 skipped`；Frontend `76 passed`
- AWS：專題 workload 為 0；本批無 AWS 寫入

## Current

- 本機 MVP P0 release gate 已全綠：正式入口、三玩家回合、結局、PostgreSQL restart、LLM recovery、polling 與 session lifecycle。
- Transfer code 為 10 分鐘一次性 hash-only；redeem 原子 rotate Player session／CSRF 並撤銷舊 session。
- 房主轉移自己的 Player 時保留原 Host session；完成房在保留期可唯讀轉移。
- 房主永久刪除有原子 repository contract、204 與三 cookie 清除；刪後所有舊 session／transfer 不可用。
- Browser 已觀察 offline→reconnected、session-expired、completed 與 console 無未處理錯誤。
- 房主可輸入 3–5 個關鍵字生成兩次可編輯 WorldDraft；失敗與 replay 仍受 inference／idempotency 成本邊界限制。
- `BedrockStoryteller` 已完成 Converse、Guardrail、schema、canonical 結果 prompt 與安全錯誤分類；production 缺 Region／model／Guardrail／token ceiling 時拒絕啟動。
- Migration/readiness Red 已保存：targeted `1 passed, 8 expected failed`；未完成 Green 已回復，工作樹不保留 production 半成品。

## Next

```text
先補 `NNN_*.sql` 必須恰為三位數 prefix 的 Red boundary
→ 重做 versioned migration CLI／PostgreSQL schema-aware readiness Green
→ retention runner
→ Nginx＋systemd release bundle、dependency lock 與去敏 logs
→ production-parity local gate／IaC Red
→ Tier 0 AWS bounded change envelope 人工核准後才可操作 AWS
```

專題已依使用者指示暫停。尚不可正式上線：migration Green、boto3 release dependency、真實 model／Guardrail、RDS readiness、TLS runtime bundle 與 AWS 驗證未完成。Residual risk：idempotency 仍是 process memory，不宣稱 multi-process exactly-once。
