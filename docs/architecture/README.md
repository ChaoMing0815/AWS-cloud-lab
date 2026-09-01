# 共演計劃：最終 production 與 future roadmap 架構

本文件呈現已部署的 Tier 0–3 課程能力與 Tier 4／5 future roadmap，不可單憑圖面判定資源已部署。依 [ADR-0008](../decisions/0008-fix-final-delivery-scope.md)，production 主線已完成至 Web／Story Worker／Data 組件化與自動部署；Tier 4／5 不是目前缺口。精確 runtime 狀態以 [`CURRENT`](../handoffs/CURRENT.md) 與[部署紀錄](../deployment-log.md)為準。

瀏覽器端的分層、API port、狀態與 AWS 安全邊界另見[前端 Clean Architecture](frontend-clean-architecture.md)。不論下方 AWS 拓撲如何演進，前端都只透過同源 API／BFF 存取後端，不直接持有 AWS credential 或呼叫 RDS、Bedrock、SQS 等服務。

## Tier 0：可玩的 Web／DB 分離版本

```mermaid
flowchart TB
    P["3–5 位玩家<br/>Web Browser"]
    subgraph AWS["AWS · ap-northeast-1"]
        B["AWS Budgets / CloudTrail"]
        BR["Amazon Bedrock<br/>AI 故事主持人"]
        CW["CloudWatch<br/>Logs / Metrics"]
        SSM["Systems Manager<br/>免 SSH 維運"]
        subgraph VPC["Amazon VPC"]
            IGW["Internet Gateway"]
            subgraph PUB["Public subnet"]
                WEB["EC2<br/>FastAPI + Web App"]
            end
            subgraph PRI["Private subnets"]
                DB["RDS PostgreSQL<br/>Public access: No"]
            end
        end
    end
    P -->|"HTTP/HTTPS"| IGW --> WEB
    WEB -->|"DB port · Web SG only"| DB
    WEB -->|"On-Demand inference"| BR
    WEB --> CW
    SSM --> WEB
    B -.-> AWS
```

驗收重點：網站可公開操作、資料庫位於 private subnet 且無 public access、只有核准的 application Security Group 可連 DB、完成一個多人回合並保存資料。PostgreSQL 已由 ADR-0003 接受，講師亦已確認題卡等價性。精確 subnet、SG、IAM、部署前關卡與清理方案見 [Tier 0 AWS 部署規劃](tier0-aws-deployment-plan.md)。

## Tier 1：可觀測性與免 SSH 維運

```mermaid
flowchart LR
    APP["Web App / API"] --> LOG["CloudWatch Logs"]
    APP --> METRIC["Metrics / Dashboard / Alarm"]
    ALARM["模擬 incident"] --> RUNBOOK["Runbook"]
    RUNBOOK --> SSM["SSM Session Manager / Run Command"]
    SSM --> APP
    LOG --> RCA["異常摘要與 Root cause analysis"]
```

驗收重點：先有 logs、metrics、dashboard、alarm，再展示 incident、診斷與 SSM 修復證據。

## Tier 2：三層運算與非同步故事處理

```mermaid
flowchart LR
    U["玩家"] --> W["Web / API compute<br/>Public application layer"]
    W --> O["PostgreSQL outbox"]
    O --> P["Publisher"]
    P --> Q["Amazon SQS + DLQ<br/>story jobs"]
    Q --> S["2 × Story Worker<br/>Private application layer"]
    W --> D["RDS PostgreSQL<br/>Private data layer"]
    S --> D
    S --> NAT["Single NAT egress"] --> BR
```

驗收重點：至少三個 AWS 運算／服務元件、public application 與 private data 分離、端到端請求、retry 與錯誤處理可展示。

## Tier 3：Container 與 CI/CD

```mermaid
flowchart LR
    G["GitHub push"] --> A["GitHub Actions<br/>test + build"]
    A -->|"OIDC short-lived role"| E["Amazon ECR"]
    E --> D["EC2 exact-digest deployment"]
    D --> H["Health check + rollback evidence"]
```

驗收重點：不保存長期 AWS key；改一行程式即可自動測試、build、部署並留下 workflow 證據。

## Future Tier 4：服務拆分與故障隔離（本次範圍外）

```mermaid
flowchart TB
    GW["Web / API Gateway"] --> L["Lobby Service"]
    GW --> C["Character Service"]
    GW --> T["Turn Service"]
    T --> R["Rules Service"]
    T --> S["Story Service"]
    S --> B["Amazon Bedrock"]
    L --> D["PostgreSQL"]
    C --> D
    T --> D
    R --> D
    S --> D
```

若未來另案啟動：Lobby、Character、Turn、Rules、Story 形成可說明的服務邊界，並展示單一服務失敗時的降級或隔離行為。這不是本次完成條件。

## Future Tier 5：Agentic AI（本次範圍外）

```mermaid
flowchart LR
    O["Orchestrator Agent"] --> N["Narrator Agent"]
    O --> R["Rules Agent"]
    O --> M["Ops Agent"]
    N --> K["RAG<br/>S3 documents + vector index"]
    M --> MCP["MCP tools<br/>read-only by default"]
    MCP --> OBS["CloudWatch / SSM"]
    O --> G["Guardrails + human approval"]
    O --> V["Prompt / token / latency / error monitoring"]
```

若未來另案啟動：Prompt 版本、RAG 引用、MCP 工具契約、多 Agent 協作、人工批准邊界，以及 token／延遲／錯誤監控均可被觀察與重現。已部署的 bounded Support Agent 不代表這個 future tier 部分完成。

## 累積演進總覽

```mermaid
flowchart LR
    T0["Tier 0<br/>Playable Web + Private DB"] --> T1["Tier 1<br/>Observability + SSM"]
    T1 --> T2["Tier 2<br/>3 components + SQS"]
    T2 --> T3["Tier 3<br/>Container + CI/CD<br/>本次最終切點"]
    T3 -. future .-> T4["Tier 4<br/>Microservices"]
    T4 --> T5["Tier 5<br/>RAG + MCP + Agents"]
```

## 全程安全與成本邊界

- 不使用 Root 進行日常開發，不建立長期 Access Key，不授予應用程式 `AdministratorAccess`。
- EC2 不開 public SSH；以 Systems Manager 維運。
- RDS 禁止 public access；Security Group 只允許必要來源。
- Tier 0 baseline 不使用 NAT Gateway；目前 private workers 共用一個受控 NAT egress。每次新增常駐服務前仍須估價並取得明確確認。
- 完成各階段證據後停止或清除不需持續運行的資源，並更新部署紀錄。
