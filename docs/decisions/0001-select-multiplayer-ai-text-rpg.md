# ADR-0001：選定多人 AI 文字 RPG 為期末專題

- 狀態：已接受
- 日期：2026-08-06
- 決策者：專題使用者

## 決策

期末專題以「部署於 AWS 的多人 AI 協作故事遊戲」作為貫穿 Tier 0–5 的單一主題，而不是另外建立互不相干的 WordPress 與 AI 專案。

產品定位：

> 由 3–5 位玩家共同輸入角色、故事背景與行動，LLM 擔任故事主持人，依遊戲狀態產生原創劇情、行動結果與下一回合情境。

## 命名與智慧財產原則

- 不使用 `Dungeons & Dragons`、`D&D`、官方 Logo 或其他可能使人誤認為官方產品的名稱。
- 優先使用自創品牌、規則、世界觀、角色、怪物、法術與美術。
- 不複製官方規則書文字、表格、地圖、劇本、美術或專有設定。
- 若未來使用 SRD，只能使用明確授權範圍內的內容，並完成授權要求的姓名標示。

## MVP 邊界

第一個可驗收版本限定為：

- 3–5 人回合制遊戲。
- 房間代碼與玩家暱稱，暫不建立完整社群帳號系統。
- 簡化角色資料、世界觀、玩家行動與劇情生成。
- 保存房間、玩家、角色、回合與劇情，重新載入後資料仍存在。
- 純文字，不做圖片、語音、戰鬥地圖與完整技能樹。
- 必須部署到 AWS，具備基本 logs、metrics、成本控管與 Demo 證據。

## 架構演進方向

Tier 0–5 為累積階段；每一層都延續同一產品、完成最小可驗證成果後再往下一層演進。

- Tier 0：可遊玩的 AWS 版 monolith、Web／DB 分層、私有資料層、LLM 劇情生成。
- Tier 1：CloudWatch、SSM 免 SSH、Parameter Store／Secrets Manager、最小權限 IAM，以及一次可重現的 AIOps incident。
- Tier 2：Web/API、Story Worker、Data 三組件，搭配 SQS、retry、網段隔離與端到端驗證。
- Tier 3：Docker、ECR、GitHub Actions OIDC 與 CI/CD。
- Tier 4：Lobby、Character、Turn、Rules、Story 服務拆分與故障隔離。
- Tier 5：Prompt 版本、RAG、Guardrails、多 Agent、tool calling、MCP、人工批准、AI 監控與 audit log。

## 後續影響

- `README.md`、Project Brief、專題規劃、甘特圖、任務清單、檢核清單、部署紀錄與架構圖仍有 WordPress 內容，後續必須分階段改寫。
- WordPress 是課程 Tier 0 題卡範例，不加入核心產品；應取得講師對自製 Web App 等效驗收方式及 Tier 0–5 對映的確認。
- 所有 AWS 建置前必須先確認 Budget Alarm、Region、現有資源、計費風險與清理計畫。
