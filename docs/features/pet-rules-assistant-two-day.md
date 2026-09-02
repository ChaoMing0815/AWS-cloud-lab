# 兩日版像素寵物規則助手

- 狀態：Merged to main（2026-09-02）；尚未 deploy
- 上游：ADR-0005、`docs/features/support-pixel-widget.md`、2026-09-01 使用者核准
- 風險：R2 可觀察 UX／規則 retrieval
- 整合基線：`0fea052af5bb60941efa6cd19c6002575cf6ff6e`
- Integrated candidate：`2a0f67993ede7c88504e2905ea1da62d9cb05dc9`
- Merged main：`add0d5ff0f9cf393b7e9323e498452c974b06170`；production 仍是 `1297a6acabaf30ca4ec2205e7641b7ab83cef781`

## 目的與誠實命名

在兩個工作日內，把已部署的像素 Support Widget 改為畫面底部的寵物式史萊姆。玩家可點選規則主題或用自然語言提問，並在保留當前頁面的對話框看到有來源回答。這是 **cited deterministic rules assistant**，不是 RAG；沒有 LLM、embedding、vector store、Bedrock、MCP 或外部提交。

## 固定共同 contract

- 前端繼續呼叫既有匿名 read-only `POST /api/v1/support/rules:lookup`，request／response schema 不變。
- 每次送出仍是獨立查詢；畫面可保留本次開啟期間的問答紀錄，但不得暗示模型記得或推論先前對話。
- `supported` 必須顯示 canonical answer 與 stable citation；`unsupported` 必須顯示固定不猜測訊息且沒有 citation。
- Player-only `local_draft_only` 草稿能力與人工確認安全文案保留；不建立外部 ticket。
- 主題捷徑固定涵蓋：開始遊戲、角色屬性、回合流程、骰點判定、星火、進度／危機／結局。捷徑只填入或直接送出正常查詢，不新增另一套答案來源。

## 前端支線：`codex/pet-rules-chat-ui`

- 史萊姆位於 viewport 底部安全區並有輕量跳動；開啟 dialog 時停止，`prefers-reduced-motion` 時完全停用。
- 點擊、鍵盤、`Esc` focus return、`aria-live`、390×844 composer／nav 不重疊與無水平 overflow 均維持。
- 對話框提供主題捷徑、使用者問題／助手回答的可辨識紀錄與 citation；不得把跨次獨立 lookup 描述為具對話記憶。
- 移除 topbar 的支援頁連結、Widget 的完整頁連結與 `/support` route composition；Backend API 與草稿能力不刪除。
- 首頁主標題以語意片語避免「都」成為逗點後孤字，並確保「下一段」不拆行；不得使用固定 `<br>` 鎖死單一寬度。至少驗證 390、768、1440 viewport contract。

## 後端支線：`codex/rules-retrieval-expansion`

- 只修改版本化 static rule records 與 deterministic matching，使上述六類主題及常見繁體中文自然問法有單一 grounded match。
- 保留 stable rule IDs、canonical content、citation、輸入界線、ambiguous／unknown fail-closed；不得以模糊 fallback 猜測最接近答案。
- 不修改 API route、schema、application service、database、dependency、runtime composition 或 AWS。

## 分支邊界與整合順序

- 精確 allowed paths 以 `.agents/work-boundaries.json` 為準；兩支線沒有共同可寫檔案。
- Feature Spec、CURRENT、approval log、governance、workflow、ops 與 AWS 只由整合 task 修改。
- 兩支線各自 strict TDD：先建立 targeted Red commit，再 Green；R2 完成時跑相關 full regression、boundary checker，建立各自短 validation manifest。
- 整合順序建議先後端 retrieval、再前端 UI；整合 task 最後跑完整 Backend／Frontend regression、390／768／1440 Browser QA，再另建 production deployment envelope。

## 不納入兩日版

- Bedrock／LLM grounded generation、embedding、vector database、真正 RAG、prompt injection model guard、跨回合聊天記憶。
- 新 IAM、AWS 資源、外部 submit、Support ticket 系統、production deploy 自動授權。

## 2026-09-01 整合驗證

- Backend 與 Frontend 支線依序無衝突合併到 `codex/final-current-reconciliation`；兩支線沒有共同修改檔案。
- 完整 Backend regression exit `0`，只有既有 Starlette／httpx deprecation warning；完整 Frontend regression `127/127`。
- Browser acceptance 已驗證 390×844、768×844、1440×900：無水平 overflow、nav／寵物不重疊，首頁中文片語不拆分。
- 390×844 Demo 的寵物 dialog 與 action composer／textarea 均不相交；開啟時動畫 paused，`Esc` focus 回到 toggle。
- `/support` 玩家導航、Widget 深連結與 route composition 已退場；規則 lookup API 與 `local_draft_only` 草稿能力保留。
- Canonical integration evidence：[`2026-09-01-pet-rules-assistant-integration`](../evidence/2026-09-01-pet-rules-assistant-integration/validation.md)。
- PR #71 與 exact-main CI run `33577514504` 已成功；合併不等於 production deployment 授權。
