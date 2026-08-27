# ADR-0005：採用 bounded Support Agent 核心

- 狀態：Accepted
- 日期：2026-08-27
- 決策者：專題使用者／整合 task
- 範圍：遊戲規則說明與問題回報草稿

## 背景

共演計劃已有靜態遊戲規則頁，但玩家遇到規則疑問或產品問題時，缺少能依問題提供精確說明與整理回報內容的互動入口。此能力可作為Tier 5 Agentic AI的提早驗證，但目前Tier 2正在修改Room／job／migration一致性，若同時接API、UI與資料庫會增加衝突與交付風險。

## 決策

先以獨立`codex/support-agent-core`分支建立不接production的Phase A核心：

1. `lookup_game_rules`只能檢索版本化、allowlisted的rule records；回答必須引用rule ID／title，找不到根據時明確標示規則未定義。
2. `draft_problem_report`只建立本機結構化草稿，包含分類、摘要、重現步驟、期望與實際結果；草稿不等於提交，後續正式submit必須再次取得使用者確認。
3. Agent只可選擇上述allowlisted能力；未知tool、額外參數、規則改寫、prompt injection與越界要求一律fail closed。
4. Knowledge、model與report repository都依application-owned ports替換；Phase A使用靜態knowledge、Mock model與memory repository，不需要LangChain或新dependency。
5. 輸入、草稿與log不得保存cookie、session／CSRF token、password、credential、runtime secret或其他敏感資料。

## 延後事項

Tier 2本地PR合併後才重新決定migration編號、PostgreSQL repository、public API、Web UI、Nova Lite／Bedrock adapter、CloudWatch metrics、rate limiting與自動部署。任何外部問題提交、AWS資源、Bedrock呼叫或production release均需新的bounded核准。

## 結果與取捨

- 優點：可平行建立Agent tool、安全與grounding contract，且不與Tier 2共用程式路徑。
- 代價：Phase A只能以本機core與Mock證明，不是線上客服功能，也不能宣稱RAG、Bedrock或問題單提交已部署。
- 後續整合必須保留人工確認、最小資料收集、引用來源與unsupported回答，不得為方便接線放寬安全邊界。
