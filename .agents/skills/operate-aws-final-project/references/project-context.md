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

## 演進順序

以下六層是同一專題的累積路線，不是互斥選項；每一層都必須有對應實作與證據：

1. Tier 0：AWS 可玩 MVP、傳統 Web／DB 分層、私有資料層、LLM 生成、基本成本與證據。
2. Tier 1：CloudWatch、SSM 免 SSH、Parameter Store／Secrets Manager、最小權限 IAM與 AIOps incident。
3. Tier 2：Web/API、Story Worker、Data 三組件，搭配 SQS、retry、網段隔離與端到端驗證。
4. Tier 3：Docker、ECR、GitHub Actions OIDC、CI/CD。
5. Tier 4：Lobby、Character、Turn、Rules、Story 服務拆分與故障隔離。
6. Tier 5：Prompt 版本、RAG、Guardrails、多 Agent、tool calling、MCP、人工批准、AI 監控與 audit log。

WordPress 是講師簡報中的 Tier 0 範例，不是目前選定產品。共演計劃應用自己的 Web／DB 分離實作對應相同能力；是否可等效取代題卡須保存講師確認。

## AWS 成本關卡

- 先驗證 Budget 告警，再建立基礎設施。
- 優先最小合理規格與可停止／刪除的架構。
- 特別標示 NAT Gateway、RDS、ALB、OpenSearch、Bedrock、長期 log retention 與跨區流量等計費面。
- 每個計費資源都記錄 owner、用途、預計清理時間與清理方式。
