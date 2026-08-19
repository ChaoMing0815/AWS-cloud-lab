# 共演計劃文件導覽

根目錄 [`README.md`](../README.md) 是對講師、同學與面試官的專案介紹；本文件才是完整技術文件入口。每日紀錄、研究、個別決策與 evidence 不直接堆疊在根 README。

## 目前狀態

- [目前 branch、驗證基準與下一步](handoffs/CURRENT.md)
- [部署紀錄](deployment-log.md)
- [Tier checkpoints](checkpoints.md)
- [甘特圖](gantt.md)

## 產品與驗收

- [文件權威索引](product/source-of-truth.md)
- [正式 MVP Spec](specs/text-rpg-mvp-spec.md)
- [Web App User Flow](product/user-flow.md)
- [Screen States](product/screen-states.md)
- [Feature Specs](features/README.md)
- [本機 MVP Test Plan](qa/local-mvp-test-plan.md)
- [Tier 0 公開試玩操作與回饋指南](qa/public-trial-guide.md)
- [產品核准紀錄](governance/approval-log.md)

## AWS 與架構

- [Tier 0–5 AWS 架構](architecture/README.md)
- [Tier 0 AWS 部署規劃](architecture/tier0-aws-deployment-plan.md)
- [Tier 0 AWS change envelope](architecture/tier0-aws-change-envelope.md)
- [AWS 服務清單](aws-services.md)
- [前端 Clean Architecture](architecture/frontend-clean-architecture.md)
- [LLM／Amazon Bedrock 串接設計](architecture/llm-integration.md)
- [Session／CSRF／Idempotency 設計](architecture/session-and-idempotency.md)
- [Console IAM bootstrap runbook](runbooks/iam-bootstrap-console.md)

## 架構決策

- [ADR-0001：多人 AI 文字 RPG](decisions/0001-select-multiplayer-ai-text-rpg.md)
- [ADR-0002：Clean Frontend Architecture](decisions/0002-adopt-clean-frontend-architecture.md)
- [ADR-0003：PostgreSQL room aggregate repository](decisions/0003-adopt-postgresql-room-aggregate-repository.md)

## 測試與證據

- [測試與嚴格 TDD 策略](testing-strategy.md)
- [驗證證據索引與保留規則](evidence/README.md)
- [AWS 截圖索引](screenshots/README.md)

Evidence 用於 milestone、R2／R3 與 AWS 驗收，不是每次測試的完整 log。一般 R1 變更以 tests 與 Git commit 留痕即可。

## 課程與規劃

- [專題計畫](project-plan.md)
- [課程要求對照](course-requirements-alignment.md)
- [任務拆分](task-list.md)
- [LLM 文字 RPG research](research/llm-text-rpg.md)
- [WordPress／自製 Web App 歷史評估](research/wordpress-web-platform-evaluation.md)

## 歷史封存

- [`daily/`](daily/)：每日工作紀錄，只供回溯，不代表目前狀態。
- [`handoffs/`](handoffs/)：歷史 handoff；目前狀態只看 `CURRENT.md`。
- Git history：詳細 debugging、Red／Green commits 與已被後續決策取代的過程。

若歷史文件與現況衝突，以[文件權威索引](product/source-of-truth.md)所列的較新、較具體且已核准文件為準。
