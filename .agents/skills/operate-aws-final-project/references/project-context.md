# 專題背景與文件路由

## 決策優先序

1. 使用者當前明確指示。
2. `docs/decisions/` 中狀態為「已接受」的 ADR。
3. 最新 handoff 與部署證據。
4. Project Brief、project plan、gantt、checkpoints、README。

若內容衝突，保留原文件並清楚標示待遷移，不得靜默混用兩套專題。

## 最新產品決策

- 主題：部署於 AWS 的多人 AI 文字 RPG。
- MVP：3–5 人回合制、房間代碼與暱稱、簡化角色與世界觀、LLM 產生原創劇情。
- 持久化：保存房間、玩家、角色、回合與劇情，重新載入後仍存在。
- 排除：圖片、語音、戰鬥地圖、完整技能樹、官方桌上角色扮演遊戲的名稱／Logo／規則內容。
- 期限：2026-09-07。

## 最終交付與未來路線

依 ADR-0008，2026-09-07 最終交付已收斂至以下 AWS production 能力：

1. 可玩 MVP、傳統 Web／DB 分層、private PostgreSQL、Bedrock 敘事與安全／成本證據。
2. CloudWatch、SSM 免 SSH、最小權限 IAM 與 bounded AIOps incident。
3. Web／API、Story Worker、Data 三組件，含 SQS／DLQ、private Worker、retry、idempotency／fencing、網段隔離與 production async E2E。
4. Docker、ECR、GitHub Actions OIDC、Trivy、SSM release、health gate 與 rollback。

Tier 4 的 Lobby／Character／Turn／Rules／Story 微服務，以及 Tier 5 的完整 Prompt／RAG／MCP／Multi-Agent／AI monitoring，只是 future roadmap／out of scope，不得當成當前缺口。

Support Agent 是後續核准平行開發並透過既有 pipeline 上線的 bounded extension；它不代表專題尚欠完整 Tier 5。

WordPress 是講師簡報中的 Tier 0 範例，不是目前選定產品。講師已確認共演計劃的 FastAPI＋private PostgreSQL 可等效對應 Web／DB 分離能力，不再列為待確認項。

## AWS 成本關卡

- 先驗證 Budget 告警，再建立基礎設施。
- 優先最小合理規格與可停止／刪除的架構。
- 特別標示 NAT Gateway、RDS、ALB、OpenSearch、Bedrock、長期 log retention 與跨區流量等計費面。
- 每個計費資源都記錄 owner、用途、預計清理時間與清理方式。
