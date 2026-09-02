# 共演計劃文件權威索引

- 狀態：Active
- Owner：專題使用者（產品）／專題開發者（技術）
- Source of Truth：是，僅負責文件權威與衝突處理
- 最後檢視：2026-09-02

## 目的

本文件只說明「哪份文件決定什麼」，不重複產品規則。若文件互相衝突，以較具體、已核准且較新的上游文件為準；程式現況不能自行覆蓋已核准規格。

## 權威順序

| 範圍 | 權威文件 | 狀態 | 下游使用者 |
| --- | --- | --- | --- |
| Agent 工作、安全與 AWS 變更關卡 | [`AGENTS.md`](../../AGENTS.md) 與專題 Skill | Active | 所有工作階段 |
| 目前 branch、驗證基準與下一步 | [`handoffs/CURRENT.md`](../handoffs/CURRENT.md) | Active | 每個新 task 的最小啟動集 |
| 選題與產品邊界 | [ADR-0001](../decisions/0001-select-multiplayer-ai-text-rpg.md) | Accepted | 產品、架構、課程對照 |
| 最終交付範圍與 Tier 4／5 future roadmap 邊界 | [ADR-0008](../decisions/0008-fix-final-delivery-scope.md) | Accepted | 所有 task、final review、Demo、架構與清理 |
| 前端與 API 責任邊界 | [ADR-0002](../decisions/0002-adopt-clean-frontend-architecture.md) | Accepted | 前端、後端、測試 |
| PostgreSQL persistence 與 repository 邊界 | [ADR-0003](../decisions/0003-adopt-postgresql-room-aggregate-repository.md) | Accepted | 後端、migration、RDS |
| Tier 2 replay-safe story result 邊界 | [ADR-0004](../decisions/0004-adopt-replay-safe-story-results.md) | Accepted | Web／API、Story Worker、Data、queue |
| Bounded Support Agent 核心邊界 | [ADR-0005](../decisions/0005-adopt-bounded-support-agent-core.md) | Accepted | 規則知識庫、客服Agent、問題回報 |
| 遊戲規則與 MVP Definition of Done | [正式 MVP Spec](../specs/text-rpg-mvp-spec.md) | Approved | User Flow、Feature Spec、測試 |
| 2026-08-09 補充產品決策 | [核准紀錄](../governance/approval-log.md) | Approved | 入口、session、LLM failure UX |
| 頁面導航 | [Web App User Flow](user-flow.md) | Active target | Screen States、入口 Feature Spec |
| 畫面狀態 | [Screen States](screen-states.md) | Active target | UI、QA |
| 實作切片 | [`docs/features/`](../features/README.md) | 各切片獨立標示 | Engineer、QA |
| 嚴格 TDD 程序 | [測試策略](../testing-strategy.md) | Active | 所有行為變更 |
| 本機 MVP 驗收範圍 | [本機 MVP Test Plan](../qa/local-mvp-test-plan.md) | Active target | QA、Release gate |
| AWS 課程交付 | [ADR-0008](../decisions/0008-fix-final-delivery-scope.md)、[Project Plan](../project-plan.md)、[Checkpoints](../checkpoints.md) | Active | 最終 Demo、架構、證據與清理 |

## 狀態規則

- `Approved／Accepted／Active` 可以指導正式實作；下游 Feature 若無新增產品差異，可標示 `Ready for TDD`，不再重複核可。
- `Active target` 表示已核准的目標行為，但不代表程式已完成。
- `Draft` 只能用於討論，不能單獨作為 production code 的依據。
- `Superseded` 必須連到替代文件，不得繼續作為驗收標準。
- Checklist 只能反映完成狀態，不能覆蓋 Spec。
- `checkpoints.md`、`task-list.md`、Gantt 或歷史 Tier 0–5 文件不得覆蓋 ADR-0008 的 final delivery scope；Tier 4／5 不是當前未完成項。
- 每次玩家可見的 patch release 都必須在同一 cohesive change 中遞增 `releaseVersion` 的 SemVer patch，並以 regression test 拒絕沿用上一版號；版本是人工 release 識別，不宣稱為 Git SHA，也不因 docs-only commit 遞增。

## 小型專案角色切換

本專題允許同一 Agent 依序扮演 PM、Designer、Engineer 與 QA。已在上游核准的 acceptance criteria 不重複詢問；驗證與證據依 [R0–R3 測試策略](../testing-strategy.md) 分級。R1 由 commits／測試摘要留痕，R2／R3 才建立 feature-level manifest；尚未完成與已知風險只在 CURRENT 或 manifest 記一次。

不要求為小型專案建立多份內容重複的 PRD／SRS／TRD；既有 MVP Spec 是產品規則主文件，Feature Spec 只描述本次差異與可驗收行為。

## Context 規則

- `handoffs/CURRENT.md` 是唯一目前狀態入口；日期 handoff 只作歷史與詳細證據。
- Handoff 只保存增量狀態、驗證基準、未完成與下一個精確起點，不重述完整專題背景。
- 若最小啟動集已足以執行任務，不再載入 README、Brief、Gantt 或完整 Checkpoints。
