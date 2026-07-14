# AWS Cloud Engineer Final Project - Project Brief

## 1. Project Background

This project is the final capstone of an AWS Cloud Engineer training program.

The goal is not simply to deploy an application to AWS. The project should evolve gradually from cloud infrastructure into DevOps, AIOps, agentic AI, and enterprise AI.

The instructor expects each stage to extend the previous one instead of becoming a separate isolated project. The architecture should grow step by step.

## 2. Core Objective

The final goal is to build an AWS-hosted AI-powered cloud operation platform.

Instead of manually maintaining cloud resources, the system should gradually evolve through the following loop:

```text
Cloud Infrastructure
  -> Monitoring
  -> AI Analysis
  -> AI Decision
  -> Automatic Operations
  -> Continuous Monitoring
```

The long-term target is a closed-loop AIOps platform.

## 3. Overall Evolution Path

The instructor repeatedly emphasized this evolution path:

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

Each phase must build on the previous phase.

## 4. Project Phases

### Phase 0: Project Governance

Deliverables:

- GitHub repository
- README
- Architecture diagram
- Milestones
- Gantt chart
- AWS budget alarm
- Documentation structure

### Phase 1: Cloud Infrastructure

Topics:

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

Deliverables:

- Running website
- Database isolation
- Architecture diagram
- AWS screenshots

### Phase 2: High Availability

Add:

- Elastic Load Balancer
- Auto Scaling

Goal:

- Support increasing traffic.

Architecture target:

```text
Internet
  -> ELB
  -> EC2
  -> EC2
  -> RDS
```

### Phase 3: Observability

Introduce:

- CloudWatch Agent
- CloudWatch Logs
- CloudWatch Metrics
- CloudWatch Dashboard
- CloudWatch Alarm

Collect:

- System logs
- Application logs
- Metrics

Visualize:

- CPU
- Memory
- Disk
- Errors

### Phase 4: AIOps

Use AI to analyze CloudWatch Logs.

Possible implementations:

- Amazon Bedrock
- LangChain
- Dify

AI capabilities:

- Summarize logs
- Detect anomalies
- Perform root cause analysis
- Suggest recovery actions

### Phase 5: AI Operations

Introduce AWS Systems Manager (SSM).

The system must not rely on SSH. AI-driven operations should use SSM to operate EC2 instances.

Example operations:

- Restart services
- Install packages
- Backup
- Reboot
- Execute Run Command operations

Instructor emphasis:

- Never rely on SSH.

### Phase 6: Knowledge Base

Build enterprise knowledge by converting the following into AI-readable knowledge:

- Documentation
- SOP
- PDF
- Wiki
- Notes

Goal:

- Instead of humans reading documentation, AI reads documentation.

### Phase 7: MCP Integration

Use the AWS official MCP Server.

Target flow:

```text
AI
  -> MCP
  -> AWS API
  -> AWS Services
```

Advanced option:

- Implement a custom MCP Server.

### Phase 8: DevOps

Implement CI/CD.

Pipeline:

```text
GitHub
  -> GitHub Actions
  -> Testing
  -> Docker Build
  -> ECR
  -> Deployment
```

Goal:

- One code push triggers automatic build and deployment.

### Phase 9: Microservices

Split monolithic applications.

Architecture evolves from one application into:

```text
Gateway
  -> Service A
  -> Service B
  -> Service C
```

Each service should support:

- Independent container
- Independent deployment
- Independent scaling

### Phase 10: Enterprise AI

Build an enterprise agent.

Features:

- Prompt management
- Knowledge Base
- RAG
- MCP
- Tool calling
- Multi-agent workflow

### Phase 11: AI Monitoring

Monitor:

- Prompt usage
- Conversations
- Token usage
- Cost
- Latency
- Model invocation

Dashboard options:

- CloudWatch
- Grafana

### Phase 12: Serverless

Gain experience using:

- Lambda
- API Gateway
- EventBridge

Learning goal:

- Understand how serverless monitoring differs from traditional server monitoring.

### Phase 13: Final Documentation

Required deliverables:

- GitHub repository
- README
- Architecture diagram
- AWS screenshots
- Success screenshots
- Demo
- Deployment instructions
- Network topology

## 5. Documentation Requirements

Minimum required documentation:

- Successful deployment screenshots
- AWS VPC screenshots
- Architecture diagram

Recommended documentation:

- Security design
- Monitoring dashboard
- High availability design
- AI workflow
- Automation flow
- Cost monitoring

## 6. AI Project Requirements

At minimum, students should be able to build an AI application that:

- Uses AWS compute
- Invokes LLMs
- Monitors model usage
- Tracks token consumption
- Monitors cost
- Monitors conversations

## 7. Future Extensions

Possible extensions:

- AI + SSM
- AI + MCP
- AI + Bedrock
- AI + Knowledge Base
- AI + CloudWatch
- AI + Serverless
- AI + CI/CD
- AI + Microservices

## 8. Final Vision

Target architecture:

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

The system should evolve into an autonomous AIOps platform capable of monitoring, analyzing, deciding, operating, and continuously improving cloud infrastructure.

## 9. Development Principles for AI Agents

AI agents such as Codex, Claude Code, Cursor, or similar tools should follow these principles when implementing this project:

1. Build incrementally: every phase extends the previous one; do not discard earlier work.
2. Prioritize working systems: a deployable, demonstrable implementation is more important than theoretical completeness.
3. AWS-first: all production artifacts must run on AWS. Local environments are for development only.
4. Infrastructure as documentation: keep architecture diagrams, screenshots, and README synchronized with implementation.
5. Automation by default: prefer Infrastructure as Code, CI/CD, and automated operations over manual procedures.
6. Security first: apply least privilege IAM, avoid exposing databases, avoid SSH where SSM is appropriate, and never hard-code secrets.
7. Observability before AI: ensure logs, metrics, and monitoring are in place before introducing AI-driven analysis.
8. Composable architecture: design services so they can evolve from monolith to microservices and eventually to AI-driven autonomous operations.

## 10. Role of This Document

This document is the project SSOT, or Single Source of Truth.

It is intended to live in the GitHub repository or project root so AI agents and human collaborators can understand the final project goal, required phases, deliverables, and development direction.
