# 共演計劃：風險式嚴格 TDD 策略

## 目的

所有 production 行為維持 test-first，但測試、review 與證據深度依風險調整。目標是證明行為由測試先定義，同時避免每個 assertion 重跑全套測試、建立獨立 evidence 或重複要求核准。

既有 2026-08-09 前的程式不追溯改寫為 TDD 成果。

## 核可來源

Approved Spec、Accepted ADR 與 approval log 已明確定義的產品行為可直接實作，不需再由 Feature Spec 重複核准。Feature Spec 只記上游未定義的差異；UTC、Clock injection、transaction、內部 API／class 拆分、fixture 與命名等可逆技術決策由 Agent 採安全預設。

只有新增／改變產品行為、上游衝突、R3 權限／成本／外部寫入／不可逆風險，或無法遵守 test-first 時需要使用者決定。

## 風險分級

| 等級 | 範圍 | 必要流程 |
| --- | --- | --- |
| R0 | 文件、註解、格式、rename、不改行為素材 | diff／必要 lint；不做 TDD evidence |
| R1 | 已核准、局部、可逆的例行行為 | targeted Red／Green＋受影響 suite；Git history 與交付摘要即證據 |
| R2 | 跨層 API、schema、repository、queue、LLM adapter、可觀察 UX | feature-level TDD；batch 完成跑 full regression；一份短 validation manifest |
| R3 | Auth、session、migration、IAM、成本、清理、不可逆或外部寫入 | R2 加負面／boundary／rollback、代表性 sensitivity 與必要 Sol 安全 review |

Browser E2E、真實 process／container restart 與 AWS 驗證放在 feature、release 或 Tier gate，不在每個小切片重跑。

## Cohesive feature／change batch 流程

### 0. Baseline

1. 確認工作樹與 branch；同一 feature 只做一次 baseline。
2. R1 跑 targeted／受影響 suite；R2／R3 跑一次相關 full regression。
3. 既有失敗不得算成 Red；只記 pass／fail 摘要與必要失敗片段。

### 1. Red

1. 從核准來源選一個可觀察行為或一組緊密相關案例。
2. 只改測試、fixture 或必要 contract，不改 production implementation。
3. 只跑 targeted test，確認因缺少目標行為產生 assertion failure；syntax、import、fixture、環境錯誤不算 Red。
4. 建立 `test(red): ...` checkpoint commit；同一 invariant 不為每個 assertion 拆 commit。

### 2. Green

1. 加入讓 Red 通過的最小 production code，不提前實作未測行為。
2. 跑 targeted tests 與受影響 suite；不在每個 Green 重跑無關 Backend／Frontend 全套。
3. 建立 `feat(green): ...` 或 `fix(green): ...` checkpoint commit。

### 3. Refactor

只在全綠後整理設計。若有實質變更，跑受影響 suite並建立 `refactor: ...` commit；沒有 refactor 時不需額外 commit、完整 regression 或「無需重構」證據。

### 4. Sensitivity

- R3：每類新 guard／invariant 選一個代表性 mutation，確認目標測試會抓到錯誤。
- R2：只有安全、狀態轉移、idempotency 或重要 boundary 需要。
- R0／R1：不強制人工 mutation。

故障注入不 commit；立即還原並重跑目標測試。R3 change batch 結束時再跑一次 full regression，不為每個 mutation 重跑全套。

### 5. Feature／merge gate

- R2／R3 的相關 Backend／Frontend／contract full regression 全綠；R1 的受影響 suite 全綠。
- 正面、負面、boundary、Browser／API／AWS 驗證符合該風險等級。
- 沒有 secret、Email、account ID、暫存檔或未還原 mutation。
- Branch tip 全綠；merge 到主要 branch、rebase、force push 仍需人工核准。

## 測試設計

- 測 public behavior 與 contract，不綁私有實作。
- Expected value 直接來自核准規格，不呼叫被測 production function 當 oracle。
- Mock 只模擬外部邊界，不複製 production algorithm。
- 重要行為涵蓋 happy path、拒絕、boundary、version conflict 或 replay 中實際相關者。
- Domain unit tests 建表格；API integration 驗證 session、headers、serialization 與 side effects；Browser E2E 不取代較低層測試。
- 測試輸出使用 quiet／dot reporter，只保存 pass／fail 數量與必要失敗片段。

## 最小證據

- R0：commit＋必要 lint。
- R1：Red／Green commits 或等價 CI artifact＋最終測試摘要；不建立 `docs/evidence` 文件。
- R2：每個 cohesive feature 一份 10–15 行 validation manifest。
- R3：在同一 manifest 增加負面／boundary／rollback、代表性 sensitivity 與 residual risk。
- AWS change batch 的 sanitized CLI output／截圖依專題 Skill 保存；本機切片不重複寫「未呼叫 AWS／費用 0」。

最小 manifest：

```markdown
# <feature／change batch> 驗證摘要
- Scope／risk／upstream source：
- Baseline：
- Red commits：
- Green／refactor commits：
- Targeted verification：
- Full regression（R2／R3）：
- Negative／sensitivity（需要時）：
- Rollback／residual risk：
```

## 文件更新責任

- `CURRENT.md`：只在 task 結束或 material state 改變時更新，保留 branch／HEAD、最近 regression、唯一 blocker、下一步與 AWS freeze。
- Feature Spec：只在產品差異或 observable contract 改變時更新。
- `checkpoints.md`：只在 milestone／Tier gate 改變時更新。
- `deployment-log.md`：只記實際 AWS／環境 change batch，不記本機每個 TDD slice。
- README：只在公開能力或 release milestone 改變時更新。
- Daily／task list：引用 commit／manifest，不重抄驗收內容。

## 停止條件

- Production code 已先改，卻沒有會因目標行為缺失而失敗的 Red。
- Red 是 syntax、import、fixture、環境錯誤或未核准 assertion。
- 為通過 Green 而放寬、刪除或改寫已核准期待。
- Required suite 未通過卻準備完成 feature、merge 或部署。
- R3／必要 R2 sensitivity 改壞實作後測試仍通過。
- Mutation、secret、debug bypass 或暫存 credentials 尚未還原／移除。

期限壓力不是跳過 test-first 或 R3 安全控制的理由；只有真正產品差異、R3 例外或無法遵守流程時才詢問使用者。
