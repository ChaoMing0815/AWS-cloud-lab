# 2026-08-09 嚴格 TDD 採用紀錄

## 決策

自本紀錄起，所有後續 production code、API、規則、adapter、IaC、workflow 與可觀察 UI 行為變更，採用可稽核的 Red／Green／Refactor TDD。

## 既有流程稽核

- 8/9 星火切片在程式開發前已有 acceptance criteria 與測試案例規劃。
- 但可執行測試與 production implementation 同在 `33699e3`，Git 歷史無法證明 executable test 先失敗。
- 因此既有成果應描述為「測試規劃先行、實作與測試交錯、完成後補強」，不得追溯宣稱為嚴格 TDD。

## 新增關卡

- Agent 開工規則加入 TDD 必讀文件與停止條件。
- 建立 Baseline、Red、Green、Refactor、Sensitivity 與 Merge gate。
- 規定功能分支、commit 命名與 evidence 模板。
- 規則、安全、授權、idempotency 與成本 guardrail 必須做刻意錯誤敏感度驗證。
- `main` 只接受最新狀態全綠的完成切片。

## 驗證

- 本次只修改治理與測試策略文件，未修改 production code。
- 已交叉連結 `AGENTS.md`、README、project plan、checkpoints、deployment log 與最新 handoff。
- 未操作 AWS，未建立資源，費用影響為 `US$0`。

## 下一個適用切片

「4／6／8 回合上限、提前完成與結局狀態」必須是第一個完整保存 Red／Green／Refactor 與 sensitivity 證據的切片。
