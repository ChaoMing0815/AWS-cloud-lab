# 共演計劃：測試與嚴格 TDD 策略

## 目的

本規範自 2026-08-09 起適用於所有後續程式開發。目的不是增加測試數字，而是以可稽核方式證明：測試先定義外部行為、實作只為滿足已核准行為，且測試確實能抓到錯誤。

既有 2026-08-09 以前的程式具有自動測試，但 Git 歷史不足以證明完整 Red／Green／Refactor，不追溯改寫為 TDD 成果。

## 適用範圍

必須使用嚴格 TDD：

- Domain rules、state machine 與 canonical state。
- Application use case、port 與 adapter contract。
- FastAPI route、authorization、CSRF、version 與 idempotency。
- Repository、migration、queue、worker 與 LLM adapter。
- 可觀察的 UI 行為、錯誤狀態、polling 與 E2E 流程。
- Terraform／CDK／CloudFormation、GitHub Actions 與維運 automation。
- 成本、安全、權限或清理 guardrail。

不強制使用 TDD：

- 純文件、註解、拼字、格式化與不改變行為的素材調整。
- 只讀 research 與架構決策。
- 一次性探索 spike；但 spike 不得直接合併，正式實作必須捨棄 spike 後重新由 Red 開始。

## 每個行為切片的強制流程

### 0. Baseline

1. 確認工作樹乾淨並建立 `codex/<feature>` 功能分支。
2. 執行相關 targeted tests 與完整 regression suite。
3. 若 baseline 已失敗，先處理或記錄既有問題，不得把既有失敗算成 Red。
4. 在 evidence 記錄測試數量、commit 與環境。

### 1. Red

1. 從 Spec／acceptance criteria 選一個最小可觀察行為。
2. 只修改測試、fixture 或測試所需 contract；不得修改 production implementation。
3. 執行 targeted test，確認至少一項因「缺少目標行為」而失敗。
4. 排除 syntax error、import error、fixture error、環境錯誤或錯誤 assertion。
5. 保存失敗指令、test name、預期與實際結果摘要。
6. 建立 `test(red): ...` commit。

### 2. Green

1. 只加入讓 Red 測試通過的最小 production code。
2. 不提前加入下一個尚無測試的行為、抽象層或容錯分支。
3. 執行 targeted test，確認轉綠。
4. 執行完整 backend、frontend 與相關 contract regression suite。
5. 建立 `feat(green): ...` 或 `fix(green): ...` commit。

### 3. Refactor

1. 在測試全綠前提下改善命名、重複、依賴方向或結構。
2. 不新增行為；若發現新行為需求，回到新的 Red cycle。
3. 重跑 targeted tests 與完整 regression suite。
4. 有實質重構時建立 `refactor: ...` commit；沒有重構則在證據註明不需要。

### 4. Test sensitivity

規則、安全、授權、權限、計費 guardrail、狀態轉移與 idempotency 變更必須進行一次敏感度驗證：

1. 暫時將門檻、operator、授權判斷或副作用保護刻意改錯。
2. 執行目標測試並確認失敗。
3. 立即還原刻意錯誤，確認完整 suite 再次全綠。
4. 不 commit 刻意錯誤；只保存變異內容與測試結果摘要。

若測試未因刻意錯誤而失敗，該測試不具足夠辨識力，必須先改善測試，不能標示完成。

### 5. Merge gate

合併前必須同時符合：

- Red、Green、Refactor／無需重構與 sensitivity 證據完整。
- 正面、負面與 boundary cases 對應 acceptance criteria。
- 完整 regression suite 全綠。
- Browser／API／AWS 驗證依該切片風險完成。
- 沒有 secret、測試帳密、Email、account ID 或暫存檔。
- 文件、checkpoint、deployment log 與 handoff 已同步。
- `main` tip 維持全綠；不得 squash 掉需要保留的 Red／Green 稽核歷史。

## 測試設計原則

- 優先測試 public behavior 與 contract，不測私有方法的實作細節。
- Expected value 使用 Spec 中的固定案例，不呼叫被測 production function 來產生 expected value。
- Mock 只模擬外部邊界，不複製 production algorithm 作為 oracle。
- 每個重要 mutation 至少涵蓋 happy path、拒絕路徑、boundary、version conflict 與 replay。
- Domain 規則以快速 unit tests 建立完整表格；API integration 驗證 session、headers、serialization 與 side effects。
- Browser E2E 驗證使用者可見流程，但不取代較低層規則測試。
- 測試名稱描述業務行為與條件，不描述目前程式寫法。

## Commit 與分支規則

建議歷史：

```text
test(red): specify max-round ending
feat(green): complete game at max round
refactor: isolate ending policy
docs(test): record ending TDD evidence
```

- 每個 Red commit 只包含測試／fixture／contract。
- 每個 Green commit 包含最小實作與必要 wiring；不修改 Red 的核心期待來迎合實作。
- 若測試期待有誤，先記錄 Spec／決策更正原因，再建立新的 Red；不得靜默降低 assertion。
- 功能分支在 Green 完成前不合併、不部署；push 前可保留 Red commit，但 branch 最新狀態必須全綠。

## Evidence 模板

每個切片在 `docs/evidence/<date>-<slice>/tdd-validation.md` 記錄：

```markdown
# <切片名稱> TDD 驗證

- Branch：
- Baseline commit：
- Acceptance criterion：

## Baseline
- 指令：
- 結果：

## Red
- Commit：
- 僅變更的測試：
- 指令：
- 預期失敗原因：
- 實際失敗摘要：

## Green
- Commit：
- 最小實作：
- Targeted test：
- Regression suite：

## Refactor
- Commit／無需重構理由：
- Regression suite：

## Sensitivity
- 暫時變異：
- 被哪個測試抓到：
- 還原後結果：

## Browser／API／AWS 驗證
- 正面：
- 負面：
- 成本與清理：
```

## 停止條件

遇到下列情況必須停止並修正流程：

- production code 已先寫，但尚無能失敗的 Red test。
- Red 是環境或測試本身壞掉，不是缺少業務行為。
- 為讓 Green 通過而刪除、放寬或改寫已核准 assertion。
- Mock 與 production code 使用同一錯誤演算法，無獨立 oracle。
- regression suite 未通過，卻準備合併、部署或標示 checkpoint 完成。
- sensitivity 驗證改壞實作後測試仍然通過。

任何例外都必須取得使用者明確同意並記錄原因；期限壓力本身不是跳過 TDD 的理由。
