# 共演計劃：多人 AI 故事遊戲

AWS 雲端工程師培訓期末專題。3–5 位玩家在同一房間提交角色行動，由 AI 故事主持人整合所有行動並產生下一回合的原創劇情。故事可以是職場、校園、日常喜劇、懸疑、科幻或奇幻，不預設單一題材。

目前優先完成不產生 AWS 費用的本機展示版本；實際 AWS 部署已獨立成延後工作流，待帳號與預算方案確認後才開始。課程要求的 Tier 0–5 是同一產品的累積演進，不是六選一。

## 本機展示

第一次建立本機環境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
```

啟動 FastAPI 與同源前端：

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload
```

開啟 `http://127.0.0.1:8000`。目前前端透過 `FetchGameApi` 呼叫 FastAPI；房間 canonical state 由伺服器端 memory repository 管理。新房間依 `DRAFT → LOBBY → COLLECTING_ACTIONS → AWAITING_HOST → AWAITING_SPARK → RESOLVING` 推進，並依規則回到下一回合、進入 `COMPLETION_AVAILABLE` 或完成為 `COMPLETED`。世界確認、開始遊戲、擲骰、回合結算與結局選擇只接受有效房主 session；3–5 位玩家必須全數完成角色與三點配點才能開始。玩家提交隱藏行動與使用屬性，房主收齊後以 `2d6 + 屬性` 產生三段結果；各玩家再選擇使用或保留星火，房主可在全員完成後結算，或明確略過等待者。正式進度、危機、星火增減、4／6／8 回合上限、提前完成與結局均由 deterministic rules 套用；`MockStoryteller` 只依已決定結果產生無費用敘事，不會修改 canonical state。Host／player 使用獨立 `HttpOnly` opaque session，mutation 檢查 CSRF、room version 與 `Idempotency-Key`；角色與 action owner 均由後端 session 決定。同一瀏覽器重新整理可恢復目前房間與玩家。3 秒無重疊 polling 已完成；離線重試與 connection UX 尚未完成。正式 Landing／router、依 room code 加入、PostgreSQL 持久化與三個獨立瀏覽器 E2E 仍待完成；目前尚未呼叫 Bedrock。AWS 資料層目前建議 private PostgreSQL，但仍要完成後端 ADR 與講師等價性確認。

根路徑現在顯示正式 Landing，提供建立、加入與次要教學 Demo 入口；`/demo` 使用隔離的 `MockGameApi` 且不保存進度。建立／加入表單尚未串接正式 API，完整目標導航與後續切片見 [Web App User Flow](docs/product/user-flow.md) 與[正式入口 Feature Spec](docs/features/entry-and-room-join.md)。

Node.js 20 以上可執行目前零第三方相依的測試：

```bash
cd web
npm test
```

後端測試：

```bash
cd backend
../.venv/bin/python -m pytest
```

後續所有程式、API、規則、IaC 與可觀察 UI 行為變更均採嚴格 Red／Green／Refactor TDD。功能分支必須先保存因缺少目標行為而失敗的 Red 證據，再進行最小 Green 實作與 Refactor；不得以開發後補測試宣稱 TDD。詳細規範見[測試與 TDD 策略](docs/testing-strategy.md)。

## MVP 範圍

- 3–5 人回合制純文字遊戲
- 房主直接輸入世界，或以 3–5 個關鍵字產生可編輯草稿
- 玩家自由建立角色，將 3 點分配至勇氣、洞察與羈絆
- 每回合提交一個隱藏行動並指定使用屬性
- 後端以 `2d6 + 屬性 + 星火` 判定成功、部分成功或失敗
- LLM 故事主持人依固定判定整合敘事，不得修改 canonical state
- 以進度、危機與 4／6／8 回合上限產生結局
- 保存房間、角色、回合、判定與故事，並支援同瀏覽器重連
- 不做圖片生成、語音、戰鬥地圖與完整帳號系統

## Tier 0–5 累積主線

- Tier 0：EC2 上的可玩 Web App／API、private PostgreSQL、Bedrock，以及 public Web／private data 隔離
- Tier 1：CloudWatch logs、metrics、dashboard、alarm、incident 與 Systems Manager 免 SSH 維運
- Tier 2：Web/API、SQS、Story Worker、private data 的三層／非同步架構
- Tier 3：Docker、Amazon ECR、GitHub Actions OIDC 與自動部署
- Tier 4：Lobby、Character、Turn、Rules、Story 服務拆分與故障隔離
- Tier 5：Prompt 版本、RAG、MCP、多 Agent、人工批准與 AI 可觀測性

WordPress 是簡報中的 Tier 0 範例與架構參考，不是目前選定的第二套產品；正式 AWS 實作前會先請講師確認自製 FastAPI＋private PostgreSQL 的等價驗收方式。

詳細內容：

- [正式 MVP Spec](docs/specs/text-rpg-mvp-spec.md)
- [文件權威索引](docs/product/source-of-truth.md)
- [Web App User Flow](docs/product/user-flow.md)
- [Screen States](docs/product/screen-states.md)
- [Feature Specs](docs/features/README.md)
- [本機 MVP Test Plan](docs/qa/local-mvp-test-plan.md)
- [產品核准紀錄](docs/governance/approval-log.md)
- [LLM 文字 RPG Research](docs/research/llm-text-rpg.md)
- [WordPress 與自製 Web App 評估](docs/research/wordpress-web-platform-evaluation.md)
- [課程簡報要求與對照方案](docs/course-requirements-alignment.md)
- [任務拆分](docs/task-list.md)
- [AWS 服務清單](docs/aws-services.md)
- [AWS 架構圖](docs/architecture/README.md)
- [前端 Clean Architecture](docs/architecture/frontend-clean-architecture.md)
- [LLM／Amazon Bedrock 串接設計](docs/architecture/llm-integration.md)
- [Session／CSRF／Idempotency 設計](docs/architecture/session-and-idempotency.md)
- [專題決策 ADR-0001](docs/decisions/0001-select-multiplayer-ai-text-rpg.md)
- [前端架構決策 ADR-0002](docs/decisions/0002-adopt-clean-frontend-architecture.md)
- [測試與嚴格 TDD 策略](docs/testing-strategy.md)
- [部署紀錄](docs/deployment-log.md)
- [2026-08-09 今日任務規劃](docs/daily/2026-08-09.md)
- [2026-08-08 完成進度與達標分析](docs/daily/2026-08-08.md)

期末專題繳交日：2026-09-07。
