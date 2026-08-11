# CURRENT：目前工作交接

- 更新日期：2026-08-11
- Branch：`codex/session-lifecycle`
- 功能基準：`1e75b69`（current-room member authorization 與 production Secure-cookie Green）
- AWS：已完成新帳號安全／IAM bootstrap 與 Tier 0 Proposed 架構規劃，未建立專題 workload；本機 Uvicorn 已停止，臨時 PostgreSQL 容器已停止並移除
- Regression：Backend `61 passed, 7 skipped`、Frontend `65 passed`

## 已完成

- Retryable storyteller failure 自動重試一次；內容拒絕不重試。
- 失敗時保存 `RESOLUTION_FAILED`，不提交 canonical rules state。
- 房主可手動 retry 或使用 deterministic fallback；一般玩家看不到 recovery controls。
- 真正終止並重啟 Uvicorn OS process 後，完整 aggregate 與原 session cookies 可還原。
- Retry attempt mutation sensitivity 已通過。
- 暫時性 network／`5xx` 保留最後 canonical 畫面，採 3／5／10 秒 bounded backoff；恢復後回到 3 秒。
- Polling `401/403` 停止並顯示 session 下一步；`409` 立即 reload canonical state。
- Polling backoff 上限 mutation sensitivity 已通過；真實 Browser 離線／reconnect release-gate 驗證仍待完成。
- 只有 local-room pointer、沒有有效 member session 時，current-room API 回 `401`，不再洩漏房間。
- `CO_STORY_COOKIE_SECURE=true` 時三個正式 cookie 都帶 `Secure`；本機 HTTP 預設維持可測。
- 兩項 session security prerequisite 均保存 Red／Green 與故障注入敏感度證據。

## AWS 目前狀態（2026-08-10 新帳號）

- Billing Console 顯示 Free plan；每月 `US$1.00` Budget 正常，2026 年 8 月預估 `USD 0.00`。
- Root MFA 已啟用且無 Root Access Key；Root 只用於低頻帳號管理，完成後應登出。
- Console-only IAM user `ming-dev` 已啟用 MFA；Access Key、API Key、CodeCommit SSH key 均為 0。
- `ming-dev` 位於 `AWSFinalProjectDevelopers`；群組只連接 `ReadOnlyAccess`、`IAMUserChangePassword`、`AWSBillingReadOnlyAccess`。
- `ming-dev` 已能唯讀帳單；更新後群組截圖已證明 Billing policy 名稱與附掛位置。
- 尚未授予 `PowerUserAccess` 或 `AdministratorAccess`，尚未建立 `AWSCourseAccountProtectionDeny`。
- Credits 精確餘額、Organization 缺席、目前 principal／Region 仍須在任何下一次 AWS 寫入前重新確認。
- 2026-08-07 Organization／Identity Center／Paid plan 紀錄屬舊帳號事故，不得當成新帳號現況。
- Tier 0 Proposed 架構採單一 public EC2、兩個 private DB subnets、Single-AZ RDS PostgreSQL、Bedrock On-Demand、SSM 與最小 CloudWatch；不採 NAT Gateway／ALB／ECS。尚未核准或部署。

證據：[`../evidence/2026-08-10-new-account-baseline/validation.md`](../evidence/2026-08-10-new-account-baseline/validation.md)

規劃：[`../architecture/tier0-aws-deployment-plan.md`](../architecture/tier0-aws-deployment-plan.md)

## 下一個精確起點

先核准 [Session lifecycle／角色轉移 Feature Spec](../features/session-lifecycle-and-transfer.md) 的精確時間與 transfer contract；未核准前不得建立 server-side expiry production Red。建議核准後依序：

```text
Clock／session expiry → activity refresh → revoke／reassign 邊界
→ 角色轉移碼錯誤、過期與 replay 負面測試
→ 成功轉移後舊 session 失效
```

三玩家 Browser E2E、LLM recovery 與 Uvicorn OS process restart 已通過；完整本機 MVP 仍不得標示 release-ready，直到真實模型 schema／Guardrail、Browser 離線／reconnect、server-side session lifecycle 與其餘 Test Plan 缺口完成。TDD 證據見 [`../evidence/2026-08-11-session-security-prerequisites/tdd-validation.md`](../evidence/2026-08-11-session-security-prerequisites/tdd-validation.md)。

下一個 AWS 起點（不與本機 MVP 切片混用）：先唯讀確認 account plan、Credits、Organizations、Region、當月費用與 principal；再審查修正版 `AWSCourseAccountProtectionDeny`。政策必須保留 Billing read，只拒絕方案升級、Organizations、Control Tower、購買／承諾與帳務寫入；完成 validation、simulation 與負面測試前不得連接 `PowerUserAccess`。

## 固定邊界

- 嚴格 Red／Green／Refactor TDD。
- 基礎功能優先，不先做外觀優化或大型重構。
- 不重問已核准 Grill 與遊戲規則。
- 未通過新帳號成本、安全與 policy 驗證關卡前，不再執行 AWS 寫入。

本階段證據見 [`../evidence/2026-08-10-polling-offline-reconnect/tdd-validation.md`](../evidence/2026-08-10-polling-offline-reconnect/tdd-validation.md)；LLM recovery 證據見 [`../evidence/2026-08-10-llm-recovery/tdd-validation.md`](../evidence/2026-08-10-llm-recovery/tdd-validation.md)。
