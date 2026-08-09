# 下一對話任務交接：完整單回合後續

- 交接日期：2026-08-09
- 期末專題繳交日：2026-09-07
- 目前分支：`main`
- AWS 寫入／新增資源／費用：無
- 本機伺服器：均已停止

## 已完成

- 狀態已可由 `AWAITING_SPARK → RESOLVING → COLLECTING_ACTIONS`。
- 玩家可選擇 `USE／DECLINE`，房主可等待全員或明確略過等待者。
- 星火造成的總值與結果重算、正式進度／危機、扣除／失敗補充均由 deterministic rules 控制。
- `MockStoryteller` 只依已決定結果產生敘事。
- 三玩家完整單回合、授權、CSRF、pending、無星火與 idempotent replay 已驗證。
- 後端 `18 passed`、前端 `28 passed`、Browser Console `0 errors`。
- 詳細證據：[星火與完整單回合驗證](../evidence/2026-08-09-spark-round-resolution/validation.md)。

## 尚未完成

- 4／6／8 回合上限、100% 提前完成、進度百分比與結局頁。
- 房主略過未提交 action、polling、取消與離線錯誤狀態。
- 三個獨立 Browser session 的人工 E2E。
- Session expiry／revoke／reassign 與 production Secure cookie。
- PostgreSQL repository、migration 與 restart persistence。
- 真實 Bedrock adapter 與全部 AWS Tier 0–5 實作。

## 下一步建議順序

1. 以純 domain function 定義進度百分比、最大回合與提前結束條件。
2. 實作 `COMPLETED`／結局 canonical state 與 Mock 結局敘事。
3. 補前端進度 meter、結局畫面與相應正負向測試。
4. 使用三個獨立 Browser session 完成全流程 E2E 並保存證據。
5. 再處理 PostgreSQL ADR；AWS 關卡通過前不部署。

## 不可違反的邊界

- 後續所有程式行為變更必須依 [`docs/testing-strategy.md`](../testing-strategy.md) 採嚴格 TDD；先保存 Red，再做 Green 與 Refactor。
- 不得將 production code 與事後補寫的測試合併描述成 test-first；規則、安全與 idempotency 必須補 mutation 敏感度證據。
- LLM 只負責敘事，不得修改骰點、結果、點數、星火或結局條件。
- AWS 部署維持暫停；不得建立／加入 AWS Organizations。
- 不建立長期 Access Key，不授予應用程式 `AdministratorAccess`。
- 每一階段都要保存正面／負面測試、Browser 驗證與部署紀錄。
