# 共演計劃最終交付檢核參考

本清單是課程能力與證據收斂的參考，不是可由未勾項自動推導的絕對 backlog。依 [ADR-0008](decisions/0008-fix-final-delivery-scope.md)，Tier 4／5 是 future roadmap，不列入本次完成條件；實際完成狀態以 [`CURRENT`](handoffs/CURRENT.md) 為準。

## 專案治理與帳號安全

- [x] 已建立並驗證專題 Agent Skill。
- [x] 新帳號已設定並驗證每月 `US$1.00` Budget；2026-08-10 當月預估 `USD 0.00`。
- [x] Root MFA 已啟用，且沒有作用中的 Root Access Key。
- [x] 已記錄誤建 AWS Organization 導致 Free plan／credits 失效的事件與矯正措施。
- [x] 本專題禁止再建立／加入 AWS Organizations。
- [x] 未建立長期 Access Key，未授予應用程式 `AdministratorAccess`。
- [x] 新帳號已建立 Console-only `ming-dev`、啟用 MFA，並確認 Access／API／SSH keys 均為 0。
- [x] `AWSFinalProjectDevelopers` 已連接 `ReadOnlyAccess`、`IAMUserChangePassword` 與 `AWSBillingReadOnlyAccess`；尚未授予 `PowerUserAccess`。
- [x] 最終部署帳號、account plan、credits、Budget、Region 與 principal 已確認；除非 change envelope 擴張，不重複驗證。
- [ ] 所有資源已有估價、owner、最大預算、停止與刪除方式。

## 產品與課程對齊

- [x] 已採用嚴格 Red／Green／Refactor TDD 規範，後續程式行為變更必須保存 test-first 與敏感度證據。
- [x] 已逐頁檢查 `docs/inbox/專題.pptx` 共 53 張。
- [x] 已完成課程 Tier 0–5 能力對照；最終交付切點另由 ADR-0008 固定。
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
- [x] Loading、Offline、Session expired、Version conflict 與 reconnect UX 已完成。
- [x] Session expiry／revoke／reassign 與 production Secure cookie 設定合約已完成。
- [x] PostgreSQL repository contract、migration、runtime composition 與 FastAPI application restart persistence 已完成。
- [x] 三個獨立 browser contexts 正式單回合 E2E 已完成。
- [x] LLM 自動／手動 retry、deterministic fallback 與正式 Uvicorn OS process restart 演練已完成。
- [x] 真實 Bedrock schema／Guardrail 驗證與 application container restart 演練已完成。
- [x] 講師已確認自製 FastAPI Web／private DB 的 Tier 0 等效檢核與課程對映。
- [x] 已以 ADR-0003 確認 FastAPI＋PostgreSQL 本機 MVP adapter；正式 AWS data service 仍須於部署前決定。
- [x] 本機 MVP P0 已通過 Spec Definition of Done；真實 Bedrock／HTTPS／container 另屬 AWS 部署 gate。

## Tier 0：AWS 可玩 MVP

- [x] VPC、public subnet、private DB subnets 與 routing 正確。
- [x] Web／API 位於 public；外部可開啟並使用。
- [x] Database 位於 private，`Public access = No` 或等效隔離。
- [x] DB SG 只允許 App SG 的必要 port。
- [x] Private DB／Data 的外網不可達與 Security Group 負面邊界已有 production 證據。
- [x] 3 位玩家可建立角色、提交 action 並完成至少一回合。
- [x] Bedrock 依固定骰子結果生成故事。
- [x] Refresh／重連後房間、角色、回合與故事仍存在。
- [x] Tier 0 架構圖、sanitized AWS 證據、README 與部署紀錄已建立；最終選片與去識別化稽核另列於交付收斂。

## Tier 1：CloudWatch、AIOps、SSM

- [x] CloudWatch 可看到 application／system logs 與基本 metrics。
- [x] Dashboard 顯示 error、latency、LLM token／retry／fallback。
- [x] 至少一個 alarm 可觸發並留下證據。
- [x] EC2 不開 public SSH；Session Manager 可連線。
- [x] Run Command 可執行受控檢查或 restart。
- [x] AIOps Agent 可讀 logs，摘要 root cause 並提出 recovery action。
- [x] 已完成一次偵測→判讀→人工批准→修復 incident Demo。

## Tier 2：三組件與網段隔離

- [x] Web/API、Story Worker、Data 組件與依賴圖完成。
- [x] 至少三個課程要求可辨識的 AWS 組件／compute 已部署。
- [x] Web 在 public；Worker／Data 在 private。
- [x] SG 串接正確，Worker／Data 外網連不到。
- [x] Queue job 有 version／idempotency，不重複扣資源或推進回合。
- [x] E2E action→worker→Bedrock→DB→result 成功。

## Tier 3：CI/CD

- [x] Current monolith 具有 runtime-only Dockerfile、自動測試與 GitHub Trivy HIGH／CRITICAL gate。
- [x] GitHub Actions 使用 OIDC，不使用長期 AWS key。
- [x] Pipeline 自動 test、build、push ECR。
- [x] Deployment 有 environment gate／最小權限 role。
- [x] 改一行 code 可自動部署並由公開頁面驗證。

## Future Tier 4：微服務（本次不驗收）

- Lobby／Character／Turn／Rules／Story 五服務與故障隔離保留為 future roadmap。
- 不把本節內容列為未完成、阻斷項或近期優先序；啟動前須重新核准範圍與成本。

## Future Tier 5：Agentic AI（本次不驗收）

- Prompt A/B、RAG、MCP／tools、多 Agent 與完整 AI observability 保留為 future roadmap。
- bounded Support Agent 已 production 上線並有 citation／拒答／人工確認證據，但不以「Tier 5 部分完成」描述。

## 最終文件與清理

- [x] 題目、系統架構、預期成效、甘特圖、檢核點已依 ADR-0008 同步。
- [ ] 已實作最終範圍有架構圖、Demo 與 README 證據。
- [ ] 成功截圖、VPC／subnet／SG／IAM／CloudWatch／SSM／CI/CD／bounded Support Agent 證據齊全。
- [ ] 沒有 secrets、token、Email 或 account ID 洩漏到 repo／截圖。
- [ ] 5–8 分鐘主 Demo 可重現，補充證據有附錄。
- [ ] Demo 後已停止／刪除資源並重新確認費用。
