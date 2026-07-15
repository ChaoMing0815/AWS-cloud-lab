# AWS 雲端工程師期末專題 Project Brief

## 1. 專案背景

本專題是 AWS 雲端工程師培訓課程的期末 Capstone。

專題目標不是單純把一個應用程式部署到 AWS，而是讓架構從雲端基礎建設逐步演進到 DevOps、AIOps、Agentic AI 與 Enterprise AI。

講師期待每個階段都能延伸前一階段的成果，而不是做成彼此孤立的小專案。整體架構應該一步一步演進。

## 2. 核心目標

最終目標是建立一個部署在 AWS 上的 AI-powered cloud operation platform。

系統應逐步從手動維護雲端資源，演進成以下閉環：

```text
Cloud Infrastructure
  -> Monitoring
  -> AI Analysis
  -> AI Decision
  -> Automatic Operations
  -> Continuous Monitoring
```

長期目標是形成一個閉環式 AIOps 平台。

## 3. 整體演進路徑

講師反覆強調的演進路徑如下：

```text
Traditional Infrastructure
  -> High Availability
  -> Observability
  -> DevOps
  -> Microservices
  -> AIOps
  -> Agentic AI
  -> Enterprise AI
```

每個 phase 都必須建立在前一個 phase 的成果上。

## 4. 專案階段

### Phase 0：專案治理

交付物：

- GitHub repository
- README
- Architecture diagram
- Milestones
- Gantt chart
- AWS Budget Alarm
- Documentation structure

### Phase 1：雲端基礎建設

主題：

- AWS VPC
- CIDR
- Public subnet
- Private subnet
- Route table
- Internet Gateway
- NAT Gateway
- EC2
- RDS
- Security Group

交付物：

- 可運作網站
- Database isolation
- Architecture diagram
- AWS screenshots

### Phase 2：高可用性

新增：

- Elastic Load Balancer
- Auto Scaling

目標：

- 支援逐漸增加的流量。

目標架構：

```text
Internet
  -> ELB
  -> EC2
  -> EC2
  -> RDS
```

### Phase 3：可觀測性

導入：

- CloudWatch Agent
- CloudWatch Logs
- CloudWatch Metrics
- CloudWatch Dashboard
- CloudWatch Alarm

蒐集：

- System logs
- Application logs
- Metrics

視覺化：

- CPU
- Memory
- Disk
- Errors

### Phase 4：AIOps

使用 AI 分析 CloudWatch Logs。

可能實作方式：

- Amazon Bedrock
- LangChain
- Dify

AI 應具備以下能力：

- 摘要 logs
- 偵測異常
- 進行 root cause analysis
- 建議 recovery actions

### Phase 5：AI Operations

導入 AWS Systems Manager，也就是 SSM。

系統不應依賴 SSH。AI-driven operations 應透過 SSM 操作 EC2。

範例操作：

- Restart services
- Install packages
- Backup
- Reboot
- Execute Run Command operations

講師強調：

- 不要依賴 SSH。

### Phase 6：Knowledge Base

建立企業知識，將以下資料轉成 AI-readable knowledge：

- Documentation
- SOP
- PDF
- Wiki
- Notes

目標：

- 不再只由人閱讀文件，而是讓 AI 讀懂文件。

### Phase 7：MCP 整合

使用 AWS official MCP Server。

目標流程：

```text
AI
  -> MCP
  -> AWS API
  -> AWS Services
```

進階選項：

- 實作 custom MCP Server。

### Phase 8：DevOps

實作 CI/CD。

Pipeline：

```text
GitHub
  -> GitHub Actions
  -> Testing
  -> Docker Build
  -> ECR
  -> Deployment
```

目標：

- 一次 code push 可以觸發自動 build 與 deployment。

### Phase 9：Microservices

拆分 monolithic applications。

架構從單一應用演進為：

```text
Gateway
  -> Service A
  -> Service B
  -> Service C
```

每個 service 應支援：

- Independent container
- Independent deployment
- Independent scaling

### Phase 10：Enterprise AI

建立 enterprise agent。

功能：

- Prompt management
- Knowledge Base
- RAG
- MCP
- Tool calling
- Multi-agent workflow

### Phase 11：AI Monitoring

監控：

- Prompt usage
- Conversations
- Token usage
- Cost
- Latency
- Model invocation

Dashboard 選項：

- CloudWatch
- Grafana

### Phase 12：Serverless

練習使用：

- Lambda
- API Gateway
- EventBridge

學習目標：

- 理解 serverless monitoring 與傳統 server monitoring 的差異。

### Phase 13：最終文件

必要交付物：

- GitHub repository
- README
- Architecture diagram
- AWS screenshots
- Success screenshots
- Demo
- Deployment instructions
- Network topology

## 5. 文件需求

最低要求：

- 成功部署截圖
- AWS VPC 截圖
- Architecture diagram

建議補充：

- Security design
- Monitoring dashboard
- High availability design
- AI workflow
- Automation flow
- Cost monitoring

## 6. AI 專題需求

最低要求是能建立一個 AI application，並具備以下能力：

- 使用 AWS compute
- 呼叫 LLMs
- 監控 model usage
- 追蹤 token consumption
- 監控 cost
- 監控 conversations

## 7. 未來延伸

可能延伸方向：

- AI + SSM
- AI + MCP
- AI + Bedrock
- AI + Knowledge Base
- AI + CloudWatch
- AI + Serverless
- AI + CI/CD
- AI + Microservices

## 8. 最終願景

目標架構：

```text
Users
  -> Application
  -> Cloud Infrastructure
  -> CloudWatch
  -> AI Analysis
  -> Knowledge Base
  -> Decision Engine
  -> MCP
  -> AWS SSM
  -> AWS Resources
  -> CloudWatch
  -> Continuous Feedback
```

系統應逐步演進成一個自主式 AIOps 平台，能夠監控、分析、決策、操作，並持續改善雲端基礎架構。

## 9. AI Agent 開發原則

使用 Codex、Claude Code、Cursor 或其他 AI Agent 實作本專案時，應遵守以下原則：

1. Incremental build：每個 phase 都延伸前一個 phase，不要推倒重做。
2. Working system first：可部署、可展示的系統比理論完整更重要。
3. AWS-first：production artifacts 必須跑在 AWS，本機環境只作為開發用途。
4. Infrastructure as documentation：架構圖、截圖與 README 要與實作同步。
5. Automation by default：優先採用 Infrastructure as Code、CI/CD 與自動化操作。
6. Security first：套用 least privilege IAM，避免資料庫暴露，不硬編 secrets，能用 SSM 時不要依賴 SSH。
7. Observability before AI：先建立 logs、metrics 與 monitoring，再導入 AI 分析。
8. Composable architecture：設計時保留從 monolith 演進到 microservices 與 autonomous operations 的可能性。

## 10. 本文件定位

本文件是專題的 SSOT，也就是 Single Source of Truth。

它應放在 GitHub repository 或專案根目錄，讓 AI Agent 與人類協作者都能理解期末專題目標、必做階段、交付物與開發方向。
