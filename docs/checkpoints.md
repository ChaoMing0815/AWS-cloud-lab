# 共演計劃 Tier 0–5 檢核清單

Demo 與每日進度依本清單逐項驗收。檔案存在不代表完成；必須有實際狀態、正面／負面測試及證據。

## 專案治理與帳號安全

- [x] 已建立並驗證專題 Agent Skill。
- [x] 新帳號已設定並驗證每月 `US$1.00` Budget；2026-08-10 當月預估 `USD 0.00`。
- [x] Root MFA 已啟用，且沒有作用中的 Root Access Key。
- [x] 已記錄誤建 AWS Organization 導致 Free plan／credits 失效的事件與矯正措施。
- [x] 本專題禁止再建立／加入 AWS Organizations。
- [x] 未建立長期 Access Key，未授予應用程式 `AdministratorAccess`。
- [x] 新帳號已建立 Console-only `ming-dev`、啟用 MFA，並確認 Access／API／SSH keys 均為 0。
- [x] `AWSFinalProjectDevelopers` 已連接 `ReadOnlyAccess`、`IAMUserChangePassword` 與 `AWSBillingReadOnlyAccess`；尚未授予 `PowerUserAccess`。
- [ ] 最終部署帳號、account plan、credits、Budget、Region 與 principal 已確認。
- [ ] 所有資源已有估價、owner、最大預算、停止與刪除方式。

## 產品與課程對齊

- [x] 已採用嚴格 Red／Green／Refactor TDD 規範，後續程式行為變更必須保存 test-first 與敏感度證據。
- [x] 已逐頁檢查 `docs/inbox/專題.pptx` 共 53 張。
- [x] 已確認 Tier 0–5 是同一主題的累積演進，不是互斥選題。
- [x] 已完成 Research、15 項訪談與正式 MVP Spec。
- [x] 已完成 Web App 補充 Grill，並確認沒有重問既有骰子、星火、角色、回合與結局規則。
- [x] 已建立文件權威索引、目標 User Flow、Screen States、入口 Feature Spec 與本機 MVP Test Plan。
- [x] 已建立題材中立的「共演計劃」展示原型。
- [x] 已接受前端 Clean Architecture、`GameApi` port 與後端 API 安全邊界。
- [x] 現有原型的第一個 vertical slice 已依 ADR-0002 遷移，遊戲 state 不再存於 `localStorage`。
- [x] 已以 `FetchGameApi` 串接 FastAPI memory repository，重新整理可恢復目前房間。
- [x] Player action 已驗證 opaque session、CSRF、room version 與 idempotency，且不接受前端指定其他 player。
- [x] Host-only 世界確認與 Lobby start 已驗證 session、CSRF、version 與 idempotency。
- [x] Player-only 角色建立、三點配點與全員角色完成 start gate 已驗證。
- [x] Action approach、`2d6 + 屬性`、三段結果與 host-only 擲骰已驗證。
- [x] 擲骰結果先保存待結算進度／危機，未繞過星火決策直接修改 canonical points。
- [x] Player-only 星火 USE／DECLINE、無星火拒絕與房主明確略過等待者已驗證。
- [x] 正式進度／危機、星火扣除／失敗補充、Mock 敘事與下一回合已由 deterministic rules 套用。
- [x] 完整單回合 replay 不重複加點、扣星火、建立故事或推進回合。
- [x] 4／6／8 回合上限、正式百分比、提前完成、host-only 結局選擇與自動結局已以嚴格 TDD 驗證。
- [x] 結局規則已通過 59／60、39／40、69／70 邊界與三項 mutation 敏感度測試。
- [x] Mock／HTTP adapter 的目標點數、提前完成與最大回合結局合約已一致，並通過 mutation 敏感度測試。
- [x] 房間狀態已使用無重疊的 3 秒 polling 同步；完成結局或停止時不再排程，並通過 Browser 驗證。
- [x] 正式 `/` 已與 `/demo` 分離；root 不載入 Demo room，Demo 不保存進度，Browser Console 0 errors。
- [x] 正式 `/` 已提供建立／加入／繼續與次要 Demo 入口，不會自動載入 `BONUS7`。
- [x] 房主建房時同時取得 Host／Player 身份並計入 3–5 位玩家。
- [x] 玩家可用 room code＋暱稱加入任意可加入房間，且錯誤／滿員／已開始案例均被拒絕。
- [ ] Loading、Offline、Session expired、Version conflict 與 reconnect UX 已完成。
- [ ] Session expiry／revoke／reassign 與 production Secure cookie 已完成。
- [x] PostgreSQL repository contract、migration、runtime composition 與 FastAPI application restart persistence 已完成。
- [x] 三個獨立 browser contexts 正式單回合 E2E 已完成。
- [x] LLM 自動／手動 retry、deterministic fallback 與正式 Uvicorn OS process restart 演練已完成。
- [ ] 真實 Bedrock schema／Guardrail 驗證與 application container restart 演練已完成。
- [ ] 講師已確認自製 FastAPI Web／private DB 的 Tier 0 等效檢核與 Tier 0–5 對映。
- [x] 已以 ADR-0003 確認 FastAPI＋PostgreSQL 本機 MVP adapter；正式 AWS data service 仍須於部署前決定。
- [ ] 本機 MVP 已通過 Spec Definition of Done。

## Tier 0：AWS 可玩 MVP

- [ ] VPC、public subnet、private DB subnets 與 routing 正確。
- [ ] Web／API 位於 public；外部可開啟並使用。
- [ ] Database 位於 private，`Public access = No` 或等效隔離。
- [ ] DB SG 只允許 App SG 的必要 port。
- [ ] 外部 DB 連線負面測試失敗。
- [ ] 3 位玩家可建立角色、提交 action 並完成至少一回合。
- [ ] Bedrock 依固定骰子結果生成故事。
- [ ] Refresh／重連後房間、角色、回合與故事仍存在。
- [ ] 架構圖、AWS 截圖、README 與部署紀錄完整。

## Tier 1：CloudWatch、AIOps、SSM

- [ ] CloudWatch 可看到 application／system logs 與基本 metrics。
- [ ] Dashboard 顯示 error、latency、LLM token／retry／fallback。
- [ ] 至少一個 alarm 可觸發並留下證據。
- [ ] EC2 不開 public SSH；Session Manager 可連線。
- [ ] Run Command 可執行受控檢查或 restart。
- [ ] AIOps Agent 可讀 logs，摘要 root cause 並提出 recovery action。
- [ ] 已完成一次偵測→判讀→人工批准→修復 incident Demo。

## Tier 2：三組件與網段隔離

- [ ] Web/API、Story Worker、Data 組件與依賴圖完成。
- [ ] 至少三個課程要求可辨識的 AWS 組件／compute 已部署。
- [ ] Web 在 public；Worker／Data 在 private。
- [ ] SG 串接正確，Worker／Data 外網連不到。
- [ ] Queue job 有 version／idempotency，不重複扣資源或推進回合。
- [ ] E2E action→worker→Bedrock→DB→result 成功。

## Tier 3：CI/CD

- [ ] Services 具有 Dockerfile 與自動測試。
- [ ] GitHub Actions 使用 OIDC，不使用長期 AWS key。
- [ ] Pipeline 自動 test、build、push ECR。
- [ ] Deployment 有 environment gate／最小權限 role。
- [ ] 改一行 code 可自動部署並由公開頁面驗證。

## Tier 4：微服務

- [ ] 已保存 monolith 故障會影響整體的 baseline。
- [ ] Lobby、Character、Turn、Rules、Story 五服務獨立部署。
- [ ] 每個服務有 health check、logs 與獨立 image。
- [ ] 停止一個服務，其餘不相關功能仍可使用。
- [ ] 服務依賴、同步／非同步邊界與故障證據完整。

## Tier 5：Agentic AI

- [ ] Prompt 有版本管理與 A/B 比較。
- [ ] RAG 可引用正確世界／規則／runbook 來源。
- [ ] MCP／tool allowlist、參數驗證與拒絕測試通過。
- [ ] Multi-Agent／多步 workflow 的責任與狀態邊界清楚。
- [ ] 高風險操作具有人工批准與 audit log。
- [ ] Dashboard 顯示 task success、token、latency、cost 與 intervention。
- [ ] 5–10 個固定案例的評估報告完成。

## 最終文件與清理

- [ ] 題目、系統架構、預期成效、甘特圖、檢核點齊全。
- [ ] 每個 Tier 有架構圖、一段 Demo 與 README 證據。
- [ ] 成功截圖、VPC／subnet／SG／IAM／CloudWatch／SSM／CI/CD／AI 監控證據齊全。
- [ ] 沒有 secrets、token、Email 或 account ID 洩漏到 repo／截圖。
- [ ] 5–8 分鐘主 Demo 可重現，完整 Tier 證據有附錄。
- [ ] Demo 後已停止／刪除資源並重新確認費用。
