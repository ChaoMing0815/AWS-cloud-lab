# ADR-0008：固定最終交付範圍為組件化與自動部署

- 狀態：Accepted
- 日期：2026-09-01
- 決策 owner：專題使用者／整合 task
- 上游核准：使用者確認最終完成目標已收斂至 AWS production 組件化與自動部署；Tier 4／5 不再是本次繳交的必須完成項

## 背景

專題初期曾以 Tier 0–5 描述可能的長期演進路線，舊版 `AGENTS.md`、Project Plan、Gantt、Checkpoints 與 Skill context 因此留有「每一 Tier 都必須實作」的敘述。

實際執行過程已由使用者調整為：

1. 完成可玩 AWS Web／private PostgreSQL 與可觀測、SSM 免 SSH 基礎。
2. 先完成 Docker／ECR／GitHub OIDC／Trivy／SSM 自動部署能力。
3. 以同一 pipeline 部署 Storyteller 品質改善。
4. 將 production 拆成 Web／API、SQS／DLQ、兩台 private Story Worker 與 private Data，完成 async 玩家 E2E、rollback 與自動部署重驗。
5. 在不與主線衝突的前提下，平行開發 bounded Support Agent，後續以已驗證 pipeline 部署成為額外產品能力。

Tier 4 五個微服務與 Tier 5 完整 Prompt／RAG／MCP／Multi-Agent 可作為未來路線，但不屬於 2026-09-07 本次交付的 Definition of Done。

## 決策

1. 本次最終交付範圍固定為：
   - AWS 可玩 MVP 與 private data layer。
   - CloudWatch／AIOps／SSM 可觀測與維運能力。
   - Web／API、Story Worker、Data 組件化，含 SQS／DLQ、private Worker、idempotency／fencing 與 production async E2E。
   - Docker／ECR／GitHub Actions OIDC／Trivy／SSM 自動部署、health gate 與 rollback。
   - 架構圖、sanitized evidence、5–8 分鐘 Demo、secrets／截圖稽核與 2026-09-08 清理 runbook。
2. Tier 0–3 名稱可繼續用於課程能力對映與架構演進說明，但完成判定以上述 production 實作與證據為主。
3. Tier 4／5 只列為 future roadmap／out of scope，不得出現在 CURRENT 的缺口、最終 checklist 的未完成項、當日優先工作或專題阻斷項。
4. Support Agent 是已核准、已部署的 bounded extension，不是「Tier 5 只完成 Phase A」。它可誠實展示 static cited rules、unsupported fail-closed、PostgreSQL `local_draft_only` 草稿、人工確認與安全邊界；不宣稱已有 RAG、MCP、external submit 或完整 Multi-Agent。
5. `docs/checkpoints.md` 與 `docs/task-list.md` 是驗收參考，不是絕對必做清單。若與本 ADR、目前 production 狀態或 sanitized evidence 衝突，以本 ADR 與已驗證實作為準。
6. 講師已確認 FastAPI＋private PostgreSQL 為 Tier 0 Web／DB 分離的等效實作，並已確認課程能力對映；不再列為待確認項。
7. 專題已改用新 AWS 帳號，舊帳號 Billing Support 禮貌性點數申請不再適用，不得重新列入 backlog 或 Demo blocker。

## 後果

- 新 task 的最小啟動文件必須可直接得到上述範圍，不需使用者再次校正 Tier 4／5、講師等效性或舊帳號點數申請。
- `CURRENT` 只保留現況、證據入口、finalization 工作與操作護欄，不再以 Tier 4／5 未實作作為 residual risk。
- Project Plan、Gantt、Checkpoints、Task List 與 Architecture Index 仍可保留 Tier 4／5 的歷史或未來圖，但必須清楚標示 `Future roadmap / Out of scope for final delivery`。
- 任何重新啟動 Tier 4、完整 Tier 5、Support Agent Bedrock／RAG／external submit 或額外 AWS 資源的作業，都是新範圍，必須另行取得使用者核准與 AWS change envelope。
