# 共演計劃：AWS 組件化與自動部署專題規劃

期末專題繳交日：2026-09-07。

## 1. 題目

> 共演計劃：部署於 AWS、由 3–5 位玩家共同遊玩的 AI 故事平台，從傳統 Web／DB 架構演進至可觀測、組件化與可自動部署的系統。

本專題只維護一個產品主題。依 [ADR-0008](decisions/0008-fix-final-delivery-scope.md)，最終交付範圍止於已部署 AWS 的可玩產品、可觀測性／SSM、Web／Story Worker／Data 組件化，以及 Docker／ECR／GitHub Actions 自動部署。Tier 4 五服務與完整 Tier 5 是 future roadmap，不是本次尚待完成項目。

## 2. 解決的問題

- 多位玩家缺少能自由輸入行動、共同推進故事的輕量工具。
- LLM 容易忘記規則或任意修改狀態，因此需要 deterministic game engine 與 canonical state。
- AI 應用上 AWS 後，還需要成本、安全、logs、部署、故障隔離與工具治理。

## 3. 產品 MVP

- 3–5 位玩家以 room code 加入。
- 自由建立角色並分配勇氣、洞察、羈絆。
- 每回合提交隱藏 action；後端以 `2d6 + attribute + spark` 判定。
- LLM 依固定判定生成共同故事，不得修改規則狀態。
- 進度、危機與 4／6／8 回合結局。
- Refresh 後資料仍存在；LLM 失敗時能 retry 或 fallback。

產品細節以 [`docs/specs/text-rpg-mvp-spec.md`](specs/text-rpg-mvp-spec.md) 為準。

## 4. 最終交付能力對照

| Tier | 目標 | 完成定義 |
| --- | --- | --- |
| 0 | 可玩的 AWS monolith 與正確 Web／DB 分層 | 公開 Web、private DB、Bedrock 一回合、資料持久化、架構與成本證據 |
| 1 | 可觀測與免 SSH 維運 | CloudWatch logs／metrics／alarm、SSM、一次 AIOps incident Demo |
| 2 | 多組件與網段隔離 | Web/API、Story Worker、Data 三組件；E2E 成功且資料層外網不可達 |
| 3 | 自動交付 | Docker、ECR、GitHub Actions OIDC，自動測試與部署成功 |

Tier 0–3 名稱保留作課程能力對照，不是要求新 Agent 逐 Tier 重新施工。Support Agent 是在既有架構與 pipeline 上完成的 bounded extension；不以「Tier 5 部分完成」描述。

## 5. 架構演進

### Tier 0

```mermaid
flowchart LR
    User["玩家瀏覽器"] --> Web["Public EC2<br/>Nginx + FastAPI monolith"]
    Web --> DB["Private PostgreSQL／RDS"]
    Web --> Bedrock["Amazon Bedrock"]
    Web --> CW["CloudWatch"]
    SSM["Systems Manager"] --> Web
```

### Tier 2

```mermaid
flowchart LR
    User["玩家"] --> API["Public<br/>Web／API"]
    API --> Publisher["Outbox Publisher"]
    Publisher --> Q["SQS + DLQ"]
    Q --> Worker["2 × Private<br/>Story Worker"]
    API --> DB["Private<br/>PostgreSQL"]
    Worker --> DB
    Worker --> Bedrock["Bedrock"]
```

### Future roadmap（本次交付範圍外）

```mermaid
flowchart LR
    Gateway["Gateway"] --> Lobby["Lobby Service"]
    Gateway --> Character["Character Service"]
    Gateway --> Turn["Turn Service"]
    Gateway --> Rules["Rules Service"]
    Gateway --> Story["Story Service"]
    Story --> RAG["RAG／pgvector"]
    Story --> Agents["Narrator／Rules／Safety Agents"]
    Agents --> MCP["MCP／允許工具"]
    Agents --> Obs["Token／Cost／Success Monitoring"]
```

## 6. 安全與成本底線

- 不建立或加入 AWS Organizations。
- 不建立長期 Access Key；GitHub 使用 OIDC。
- Root 只做帳號層級必要操作並啟用 MFA。
- 不授予應用程式 `AdministratorAccess` 或服務 Full Access。
- 不開 public SSH；使用 SSM。
- Database、worker 與內部服務不直接對外。
- 每個計費資源先估價並記錄 owner、用途、停止與刪除方式。
- 高 Tier 資源只在驗證／Demo 時啟動，保存證據後立即縮減。

## 6.1 開發品質底線

- 所有 production code、API、遊戲規則、資料 adapter、IaC、CI/CD workflow 與可觀察 UI 行為變更採嚴格 TDD。
- 每個小型行為切片依序完成 Red、Green、Refactor，並將失敗／成功輸出保存至 `docs/evidence/`。
- `main` 只接收 regression suite 全綠的完成切片；不以事後補測試冒充 TDD。
- 規則、安全、授權、計費防護與 idempotency 必須額外證明測試對刻意錯誤敏感。
- 詳細流程與例外見 [`docs/testing-strategy.md`](testing-strategy.md)。

## 7. 預期成效

- 展示同一產品如何由 monolith 演進為可維運、多組件與 CI/CD 架構。
- 證明網段、SG、IAM、SSM、CloudWatch 與資料隔離。
- 證明故事生成與 Support Agent 都有明確輸入、引用、拒答及人工確認邊界。
- 建立可向講師與面試官說明的 AWS 架構演進與自動部署證據。

## 8. Demo 主線

1. 展示 Tier 0 三位玩家完成一回合與資料持久化。
2. 展示 public Web／private DB、SG 與 DB 外網連線失敗。
3. 模擬服務錯誤，由 CloudWatch 偵測、AI 摘要，再以 SSM 受控處理。
4. 展示三組件架構與非同步 Story Worker。
5. 改一行版本文字，觸發 GitHub Actions 自動部署。
6. 展示 Support Agent 的 supported citation、unsupported 不猜測與 `local_draft_only` 人工確認草稿。
7. 展示 GitHub Actions 以 exact digest 部署、健康檢查與 rollback 能力。

## 9. 必備交付

- 題目與預期成效。
- 已實作範圍的 production architecture diagram；future roadmap 若出現必須明確標示範圍外。
- 甘特圖與驗收參考 checkpoints。
- GitHub README、部署步驟與清理方式。
- AWS 成功截圖、VPC／subnet／SG／IAM／CloudWatch／SSM／CI/CD 與 bounded Support Agent 證據。
- 5–8 分鐘主 Demo；補充證據可放附錄或錄影。

## 10. 已固定的交付邊界

- 講師已確認 FastAPI＋private PostgreSQL 的 Tier 0 等效性與課程對映，不得再列為待辦。
- PostgreSQL／RDS private data layer 已由 ADR-0003 接受。
- 最終交付範圍依 ADR-0008；Tier 4／5 只有 future roadmap 意義。
- 新增常駐 AWS 資源、Bedrock／RAG 呼叫或其他成本 envelope 擴張，仍須另行核准。
