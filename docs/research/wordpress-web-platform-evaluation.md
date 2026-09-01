# 共演計劃：WordPress 與自製 Web App 評估

- 日期：2026-08-07
- 狀態：歷史研究；WordPress 不列為核心或預設保底，最終交付範圍已由 ADR-0008 收斂至 AWS 組件化與自動部署
- 範圍：本機 MVP 與後續 AWS Tier 0
- AWS 變更：無

## 1. 結論

WordPress 技術上可以實作本專案，但不建議把它當成核心多人遊戲後端。

推薦方案：

```text
Browser
  -> Vanilla HTML／CSS／JavaScript
  -> FastAPI JSON API
  -> Repository interface
       -> Local repository（開發與測試）
       -> PostgreSQL repository（AWS 建議，待 ADR）
  -> Story engine
       -> Deterministic dice／state rules
       -> Local mock storyteller
       -> Amazon Bedrock adapter（AWS）
```

第一版保留現有 `web/` 的 Vanilla JavaScript，不立即導入 React、Vue 或前端 build tool。FastAPI 同時提供靜態檔案與 `/api/v1`，部署時只需維護一個 application process。FastAPI 官方支援掛載靜態前端，並提供 request model、validation、OpenAPI 與測試介面，適合把正式 Spec 轉成可驗證 API。[FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)／[FastAPI Reference](https://fastapi.tiangolo.com/reference/)

## 2. WordPress 是否可行

可以。WordPress REST API 能讓 theme、plugin 或獨立 JavaScript frontend 交換 JSON，也支援註冊 custom endpoint。[WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)／[Adding Custom Endpoints](https://developer.wordpress.org/rest-api/extending-the-rest-api/adding-custom-endpoints/)

若採 WordPress，至少必須自行開發一個 plugin，負責：

- 房間、玩家、角色、action、回合與事件資料表。
- 房主與玩家的 opaque session token。
- 自訂 REST endpoints、參數驗證與 `permission_callback`。
- 行動 revision、room version、idempotency 與重複結算防護。
- 骰子、星火、進度、危機與結局規則。
- Bedrock 呼叫、structured output、timeout、retry 與 fallback。
- 7 天清理、永久刪除、log redaction 與測試。

WordPress 官方說明 plugin 可建立自己的 MySQL／MariaDB tables；這代表本專案仍需設計與維護完整資料模型，而不是安裝 WordPress 就自動得到遊戲功能。[Creating Tables with Plugins](https://developer.wordpress.org/plugins/creating-tables-with-plugins/)

## 3. 不建議 WordPress 作為核心的原因

| 評估面 | WordPress 核心遊戲 | 自製 FastAPI App |
| --- | --- | --- |
| 現有進度 | 需改寫成 PHP theme／plugin 或把前端嵌入 WordPress | 可直接延續現有 `web/` |
| 遊戲狀態 | 需自行設計 custom tables、locking 與 transaction | 依正式 Spec 建立 domain model 與 repository |
| Session | WordPress 帳號系統不符合「無 Email／密碼」設計，仍需自製 | 可直接實作 opaque cookie session |
| 併發與 idempotency | 必須自行在 MySQL／PHP 實作 | 可用 room version、transaction 與 unique constraint 實作 |
| LLM 整合 | 需自行寫 PHP AWS SDK adapter 與 retry | Python `boto3` 可直接使用 Bedrock Runtime |
| AWS 資料層 | WordPress 需要 MySQL／MariaDB | 可使用 private PostgreSQL 展示 Web／DB 分離並延續後續服務拆分 |
| 維護面 | WordPress core、theme、plugin、PHP 與 DB 都要更新 | 維護單一專題 application |
| 展示價值 | 容易被看成 CMS 客製 plugin | 能直接展示 API、狀態機、AI 與 AWS 整合能力 |

WordPress 官方目前建議 PHP 8.3+、MariaDB 10.11+ 或 MySQL 8.0+，並要求 HTTPS。[WordPress Requirements](https://wordpress.org/about/requirements/) 若在 AWS 維持 Web／DB 分離，通常還會重新引入 RDS 的持續費用與管理工作；若把資料庫裝在同一台 EC2，又無法展示原規劃的 private DB isolation。

## 4. 推薦 Web App 分層

### 4.1 Frontend

保留：

- `web/index.html`
- `web/styles.css`
- `web/app.js`

逐步把單一 `app.js` 拆成：

```text
web/js/api.js
web/js/state.js
web/js/views.js
web/js/host.js
web/js/player.js
```

Frontend 只負責畫面、表單、polling 與顯示結果；不得在瀏覽器決定骰子、星火、進度或房主權限。

### 4.2 Backend

建議使用 Python FastAPI：

- Pydantic models 對應 Spec request／response schema。
- `/api/v1/rooms`、players、actions、roll、spark、resolve 與 delete endpoints。
- 伺服器端 session cookie 與 authorization。
- Deterministic game engine。
- Repository interface。
- Storyteller interface。
- Structured logs、health endpoint 與 pytest。

### 4.3 本機與 AWS adapters

```text
Repository
  ├─ Memory／SQLite：本機開發
  └─ PostgreSQL：AWS 部署建議（待 ADR）

Storyteller
  ├─ Deterministic mock：本機與自動測試
  └─ Amazon Bedrock Converse：AWS 部署
```

Bedrock Converse 提供跨支援模型的一致 messages 介面；呼叫需要 `bedrock:InvokeModel`，應由 EC2 role 限定指定模型，而不是使用長期 Access Key。[Boto3 Bedrock Converse](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/converse.html)

PostgreSQL 可透過 transaction、row lock、unique constraint 與 `room.version` 實作回合一致性與 idempotency。資料存取仍須包在 repository interface 後，避免本機與 AWS 實作綁死。

## 5. WordPress 的合理使用位置

課程簡報把 WordPress Web／DB 分離列為 Tier 0 範例路線之一；後續已確認「共演計劃」的 FastAPI＋private PostgreSQL 可等效展示 public Web／private DB、資料持久化與網路隔離能力。本研究中的早期 Tier 0–5 推論已由 ADR-0008 取代：

```text
FastAPI Web App：公開展示入口與遊戲 API
PostgreSQL：private subnet 內的持久化資料層
```

WordPress 只保留為歷史技術評估，不加入交付範圍。講師已確認 FastAPI＋private PostgreSQL 可作為 Web／DB 分離的等價成果，不得再要求重問。完整對照見[課程簡報要求與對照方案](../course-requirements-alignment.md)。

## 6. 實作順序

1. 將現有奇幻導向展示改成題材中立的「共演計劃」。
2. 建立 FastAPI application skeleton、health endpoint 與靜態檔案服務。
3. 依 Spec 建立 Pydantic domain／API models。
4. 建立 memory repository 與 deterministic game engine。
5. 把 `localStorage` mutation 改成呼叫 API；保留 UI-only preferences。
6. 加入 mock storyteller，完成 3 位玩家的一回合整合測試。
7. 加入 retry、fallback、session、刪除與 log redaction 測試。
8. 講師、AWS 帳號與預算確認後，再加入 PostgreSQL 與 Bedrock adapters。

## 7. 決策關卡

開始建立 AWS adapter 前需要確認：

- 核心遊戲採「Vanilla JS＋FastAPI」，不預設另建 WordPress。
- 向講師確認「自製 FastAPI＋private PostgreSQL」是否完整對應 Tier 0 Web／DB 分離驗收。
- 本機 repository 第一版使用記憶體或 SQLite；AWS adapter 建議 RDS PostgreSQL，需另立正式 ADR。

在使用者確認前，本文件只代表推薦方案，不是已接受 ADR。
