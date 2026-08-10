# CURRENT：目前工作交接

- 更新日期：2026-08-10
- Branch：`codex/llm-recovery-and-process-restart`
- 功能基準：`3dfff89`（LLM recovery、房主 UI 與 Uvicorn OS process restart 已完成）
- AWS：已完成新帳號安全／IAM bootstrap，未建立專題 workload；本機 Uvicorn 已停止，臨時 PostgreSQL 容器已停止並移除
- Regression：Backend `66 passed`、Frontend `60 passed`

## 已完成

- Retryable storyteller failure 自動重試一次；內容拒絕不重試。
- 失敗時保存 `RESOLUTION_FAILED`，不提交 canonical rules state。
- 房主可手動 retry 或使用 deterministic fallback；一般玩家看不到 recovery controls。
- 真正終止並重啟 Uvicorn OS process 後，完整 aggregate 與原 session cookies 可還原。
- Retry attempt mutation sensitivity 已通過。

## AWS 目前狀態（2026-08-10 新帳號）

- Billing Console 顯示 Free plan；每月 `US$1.00` Budget 正常，2026 年 8 月預估 `USD 0.00`。
- Root MFA 已啟用且無 Root Access Key；Root 只用於低頻帳號管理，完成後應登出。
- Console-only IAM user `ming-dev` 已啟用 MFA；Access Key、API Key、CodeCommit SSH key 均為 0。
- `ming-dev` 位於 `AWSFinalProjectDevelopers`；群組只連接 `ReadOnlyAccess`、`IAMUserChangePassword`。
- `ming-dev` 已能唯讀帳單，但實際 Billing policy 與附掛位置尚待下次 AWS 唯讀盤點確認。
- 尚未授予 `PowerUserAccess` 或 `AdministratorAccess`，尚未建立 `AWSCourseAccountProtectionDeny`。
- Credits 精確餘額、Organization 缺席、目前 principal／Region 仍須在任何下一次 AWS 寫入前重新確認。
- 2026-08-07 Organization／Identity Center／Paid plan 紀錄屬舊帳號事故，不得當成新帳號現況。

證據：[`../evidence/2026-08-10-new-account-baseline/validation.md`](../evidence/2026-08-10-new-account-baseline/validation.md)

## 下一個精確起點

依本機 MVP Test Plan，下一個基礎切片處理 polling 離線／reconnect UX：

```text
暫時性網路／5xx → 3／5／10 秒 bounded backoff
→ 保留最後 canonical 畫面 → 恢復後回到 3 秒 polling
→ 401／403 停止 retry；409 重新載入 canonical state
```

三玩家 Browser E2E、LLM recovery 與 Uvicorn OS process restart 已通過；完整本機 MVP 仍不得標示 release-ready，直到真實模型 schema／Guardrail、離線 UX、session lifecycle 與其餘 Test Plan 缺口完成。

下一個 AWS 起點（不與本機 MVP 切片混用）：先唯讀確認 account plan、Credits、Organizations、Region、當月費用與 principal；再審查修正版 `AWSCourseAccountProtectionDeny`。政策必須保留 Billing read，只拒絕方案升級、Organizations、Control Tower、購買／承諾與帳務寫入；完成 validation、simulation 與負面測試前不得連接 `PowerUserAccess`。

## 固定邊界

- 嚴格 Red／Green／Refactor TDD。
- 基礎功能優先，不先做外觀優化或大型重構。
- 不重問已核准 Grill 與遊戲規則。
- 未通過新帳號成本、安全與 policy 驗證關卡前，不再執行 AWS 寫入。

本階段證據見 [`../evidence/2026-08-10-llm-recovery/tdd-validation.md`](../evidence/2026-08-10-llm-recovery/tdd-validation.md)；PostgreSQL 設計證據見 [`../evidence/2026-08-10-postgres-persistence/tdd-validation.md`](../evidence/2026-08-10-postgres-persistence/tdd-validation.md)。
