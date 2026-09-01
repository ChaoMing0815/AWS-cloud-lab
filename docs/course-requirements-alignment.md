# 課程簡報要求與「共演計劃」Tier 0–5 對照

- 分析日期：2026-08-07
- 原始資料：[`docs/inbox/專題.pptx`](inbox/專題.pptx)，共 53 張投影片
- 原始檔 SHA-256：`8ad62fe7dbf46f9c532219f2fa87e7053271aecd241383bc55e771da9e4d42c8`
- 解讀依據：使用者澄清、`AGENTS.md`、Project Brief、ADR-0001
- 狀態：歷史課程能力對照；最終交付範圍以 [ADR-0008](decisions/0008-fix-final-delivery-scope.md) 為準
- AWS 變更：無

## 1. 更正紀錄

先前把「完成 Tier 0 任一題即可達及格門檻」誤讀為 Tier 0–5 是選擇題，並因此推薦另外加入 WordPress 保底。這不符合 Project Brief 所描述的架構演進目標，也不符合使用者提供的課程上下文。

當時建立的課程能力對照：

```text
同一個產品主題
  → Tier 0 傳統雲端架構
  → Tier 1 維運、可觀測性與安全操作
  → Tier 2 多組件分離
  → Tier 3 CI/CD
  → Tier 4 微服務
  → Tier 5 Enterprise Agentic AI
```

投影片中的 WordPress、CS、LINE Bot 等是用來說明能力與檢核點的題卡，而不是必須逐字實作的產品清單。共演計劃沿用同一產品完成 Tier 0–3 對應的 production 能力；Tier 4／5 保留為 future roadmap，不是本次未完成項目或 Demo 阻斷項。

## 2. 全階段共同要求

| 要求 | 來源 | 共演計劃做法 |
| --- | --- | --- |
| 所有成果最終部署到 AWS | 投影片 4、8、51；Project Brief | 最終範圍內的產品、組件化、維運與自動部署皆保存 AWS 實作與驗證，不能只交本機 Demo |
| 能跑與架構正確是基本門檻 | 投影片 4、5、51 | 先完成 Tier 0 可玩 vertical slice，再向上演進 |
| 控制費用、設 Budget、Demo 後清理 | 投影片 4、9 | 每層先估價，採最小規格與短時展示；不得建立／加入 Organization |
| 同一架構逐步演進 | Project Brief、AGENTS.md | 不另建孤立 WordPress 專案；所有能力回到共演計劃 |
| 五項必備文件 | 投影片 10–13 | 題目、架構、預期成效、甘特圖、檢核點同步更新 |
| GitHub 與可視化證據 | 投影片 5、6、51 | 已實作範圍保存架構圖、Demo、README、成功與負面測試證據 |

## 3. 歷史 Tier 0–5 能力對照

下表用於說明課程演進概念，不等同目前 task list。Tier 0–3 已落實為本次 production 主線；Tier 4／5 僅供未來擴充參考。

| Tier | 最小可驗證實作 | 主要技術 | Demo 證據 |
| --- | --- | --- | --- |
| 0：傳統架構 | 3–5 人可完成至少一回合；Web 公開、DB 私有、資料可持久化 | VPC、public EC2、private PostgreSQL／RDS、SG、Bedrock | 公開 URL、VPC／subnet、DB 外網失敗、遊戲 refresh 後仍存在 |
| 1：維運層 | logs／metrics／alarm；SSM 免 SSH；AI 分析一次故障並提出處置 | CloudWatch、SSM、Parameter Store、AIOps／LangChain | 模擬 500 或 DB 失敗，展示偵測→判讀→受控修復 |
| 2：組件切割 | 將 monolith 拆成 Web/API、Story Worker、Data 三個組件並隔離網段 | 至少 3 個 AWS compute／EC2、SQS、public/private subnet、SG | 依賴圖、三組件狀態、資料層外網失敗、E2E 故事生成 |
| 3：CI/CD | 改一行程式後自動測試、build、推送與部署 | Docker、ECR、GitHub Actions OIDC、EC2／ECS | commit→tests→image→deploy→新版本頁面 |
| 4：微服務 | 從 monolith 拆出五個服務；單一服務故障不拖垮全部 | Lobby、Character、Turn、Rules、Story services；ECS／containers | 故意停止 Story service，Lobby／Character／既有查詢仍可用 |
| 5：Agentic AI | Prompt 版本、RAG、MCP／工具、多 Agent、人工批准與 AI 監控 | LangChain／Bedrock、pgvector、MCP、CloudWatch dashboard | 引用規則／世界資料、受控工具呼叫、token／cost／success dashboard |

## 4. Tier 0 起始架構

```mermaid
flowchart LR
    U["3–5 位玩家"] --> IGW["Internet Gateway"]
    IGW --> APP["Public Subnet<br/>EC2：Nginx + FastAPI monolith"]
    APP -->|"DB port<br/>source = App SG"| DB["Private DB Subnets<br/>PostgreSQL／RDS"]
    APP -->|"限量 inference"| BR["Amazon Bedrock"]
    APP --> CW["CloudWatch 基本 logs／metrics"]
    SSM["Systems Manager"] --> APP
```

Tier 0 即應保留的安全邊界：

- Database 不公開，外網連線負面測試必須失敗。
- EC2 不開 `22/tcp`；人員維運使用 SSM。
- 應用 role 只允許指定 log、parameter、database secret 與 Bedrock model。
- 不使用長期 Access Key，不授予應用程式 `AdministratorAccess`。
- 遊戲規則由後端決定，LLM 只能生成受 schema 限制的敘事。

## 5. 課程演進圖與最終交付切點

```mermaid
flowchart LR
    T0["Tier 0<br/>FastAPI monolith<br/>private PostgreSQL"] --> T1["Tier 1<br/>CloudWatch + SSM<br/>AIOps"]
    T1 --> T2["Tier 2<br/>Web/API + Worker + Data<br/>SQS"]
    T2 --> T3["Tier 3<br/>Docker + ECR<br/>GitHub Actions<br/>本次最終切點"]
    T3 -. future .-> T4["Tier 4<br/>五個獨立服務<br/>故障隔離"]
    T4 --> T5["Tier 5<br/>RAG + MCP + Multi-Agent<br/>AI Observability"]
```

演進原則：

- 已完成的演進沿用同一產品、程式、資料與證據，不重做另一個產品。
- ADR-0008 固定本次交付切點，不能由這份歷史對照反推出 Tier 4／5 待辦。
- future roadmap 若日後啟動，仍須重新核准範圍、成本與 AWS change envelope。

## 6. WordPress 的位置

WordPress 不加入共演計劃核心架構。它提供的教學重點是：

- Web 對外、DB 隱藏。
- Public／private subnet。
- SG-to-SG 僅開必要 DB port。
- 寫入資料後仍可持久化。

共演計劃以 FastAPI Web App 與 private PostgreSQL 實作同一組 Tier 0 能力；講師已確認其等效性與課程對映。不得再把 WordPress 或講師確認列為待辦。

## 7. Future Tier 5 邊界（本次範圍外）

目前 MVP 的 LLM 故事生成只是生成式 AI，不因呼叫 Bedrock 就自動成為 Agentic AI。到 Tier 5 才加入：

- Prompt 版本與 A/B 評估。
- 世界設定、規則、事件摘要或維運 runbook 的 RAG。
- 受 allowlist 限制的 MCP／tool calling。
- Narrator、Rules Auditor、Safety Reviewer 等明確分工。
- 高風險操作需要人工批准。
- 任務成功率、token、latency、cost、Guardrail intervention 與 tool audit log。

## 8. 已確認事項

講師已確認自製 FastAPI Web App＋private PostgreSQL 可作為 Web／DB 分離的等效實作，課程能力對映亦已確認。此項不是待決策、待詢問或 Demo 阻斷項。

## 9. 目前固定邊界

1. PostgreSQL／RDS private data layer 已由 ADR-0003 接受並部署。
2. 最終交付範圍依 ADR-0008，止於 production 組件化與自動部署。
3. Support Agent 是 bounded deployed extension，不代表 Tier 5 尚待補完。
4. Tier 4／5 或新 AWS／Bedrock 資源只有在新的範圍與成本核准後才可啟動。
