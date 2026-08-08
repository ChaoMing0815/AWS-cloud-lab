# ADR-0002：前端採 Clean Architecture 與後端 API 邊界

- 狀態：Accepted
- 日期：2026-08-08
- 決策者：專題開發者

## 背景

現有 `web/app.js` 是可展示的 Vanilla JavaScript 原型，但畫面事件、遊戲流程、假資料與 `localStorage` 持久化集中在同一處。若直接在頁面中加入 Bedrock、RDS、SQS 或 AWS SDK，會讓瀏覽器持有不應公開的服務細節與 credential，也會使 Tier 0–5 每次演進都重寫前端。

正式 MVP Spec 已把遊戲規則、canonical state、principal 與 idempotency 定義為伺服器責任，因此需要先固定前端與 AWS 的責任邊界。

## 決策

1. 前端採 `UI → Application → Domain` 的 inward dependency rule。
2. Application 定義 `GameApi`、preferences、polling、telemetry 與 clock ports；外層 adapter 實作它們。
3. 正式網路存取集中於 `FetchGameApi`；本機 UI 以相同契約的 `MockGameApi` 開發與測試。
4. 瀏覽器只呼叫同源 `/api/v1`，不直接呼叫 RDS、Bedrock、SQS、CloudWatch、SSM、Secrets Manager 或 IAM。
5. 不在前端放 AWS SDK、Access Key、secret 或可由 JavaScript 讀取的長期 session token。
6. 後端是房間、角色、行動、骰子、進度、危機與結局的唯一 canonical state；`localStorage` 只保存非敏感 UI preferences。
7. Host／player session 使用後端簽發的安全 cookie；mutation 必須配合 server-side authorization、room version 與 idempotency。
8. MVP 保留 Vanilla JavaScript，改用原生 ES modules 與 composition root；暫不引入 React 或大型 bundler。
9. Tier 4 即使拆成微服務，瀏覽器仍透過單一 API／BFF，避免 UI 綁定內部服務拓撲。

詳細分層、目錄、狀態管理、測試與遷移方式見[前端 Clean Architecture](../architecture/frontend-clean-architecture.md)。

## 理由

- 防止 AWS credential 或服務權限進入不可信任的瀏覽器環境。
- 讓 Mock、FastAPI、EC2、SQS worker 與微服務共享相同前端 use case。
- 能獨立測試遊戲流程、錯誤處理、輪詢與 idempotency。
- 保留目前無 build step 的開發速度，並為未來替換 UI framework 留出邊界。

## 後果

正面：

- AWS 後端演進不需要同步重寫所有頁面。
- `fetch`、`localStorage`、polling 與 telemetry 有單一可稽核位置。
- 本機可先用 Mock 完成畫面與流程，不產生 AWS 費用。
- 更容易建立三玩家 E2E 與未授權／重複操作負面測試。

代價：

- 相較單一 `app.js`，檔案與介面數量增加。
- API DTO 到 ViewModel 需要 mapping。
- 團隊必須遵守「UI 不繞過 use case／port」的規則。

## 未採用方案

- 繼續以單一 `app.js`＋`localStorage` 作正式產品：無法建立可信任的多人 canonical state。
- 從瀏覽器直接使用 AWS SDK：會擴大 credential、CORS、IAM 與濫用風險。
- 現在立即改成 React／Next.js：目前 UI 複雜度不足以抵銷工具鏈與遷移成本；未來仍可替換 UI 外層。
- 為每個未來微服務建立獨立前端 client：會過早暴露內部拓撲並提高 Tier 4 遷移成本。

## 後續工作

- 先建立 `GameApi` contract 與 `MockGameApi`，再拆分現有頁面。
- 建立 FastAPI skeleton 後實作 `FetchGameApi`。
- 為 runtime config、cookie、CSRF、room version 與 idempotency 寫 contract tests。
- 在 AWS 部署前確認帳號、Budget、估價與 principal；本 ADR 不授權任何 AWS 寫入。
