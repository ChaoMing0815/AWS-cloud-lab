# Support Agent API／Web Integration Contract

- 狀態：Ready for strict TDD
- 上游：ADR-0005、Bounded Support Agent Phase A、PostgreSQL Draft persistence
- 風險：API／UI為R2；session、CSRF、rate limit與identity為R3

## 本輪目標

將既有static cited rules與PostgreSQL `local_draft_only`草稿接到同源API與Web UI。此切片不新增migration、不呼叫Bedrock、不建立RAG，也沒有GitHub Issue、Email或其他外部submit能力。

## HTTP contract

### 規則查詢

```http
POST /api/v1/support/rules:lookup
Content-Type: application/json

{"message":"星火什麼時候可以使用？"}
```

- 可匿名使用；`message`正規化後為1–500字元。
- JSON request body上限為1024 bytes；只接受`message`欄位，未知欄位回固定`422`。
- `supported`回傳canonical answer與至少一筆`ruleId`、`title`、`sourceSection`、`sourceVersion`引用。
- `unsupported`使用既有固定回答且citations為空；不得由API或UI補寫規則。

固定response為：

```json
{
  "status": "supported",
  "answer": "canonical rule content",
  "citations": [
    {
      "ruleId": "spark-usage",
      "title": "星火的用途",
      "sourceSection": "正式 MVP Spec §10 星火",
      "sourceVersion": "mvp-v1"
    }
  ]
}
```

`unsupported`使用相同三個頂層欄位，`status="unsupported"`、`answer`為既有固定回答、`citations=[]`。兩種結果都不得增加domain `reason`或其他欄位。

### 問題草稿

```http
POST /api/v1/support/reports:draft
Content-Type: application/json
X-CSRF-Token: <player csrf>

{"description":"重現步驟與預期／實際結果"}
```

- 必須有有效current Room與Player session；房主以其Player session建立草稿，Host session本身不代替Player identity。
- `description`正規化後為1–2000字元。Reporter identity只由server以canonical room ID＋player ID衍生；request不得接受player ID、identity hash、report ID、submission state或human-confirmation flag。
- JSON request body上限為4096 bytes；只接受`description`欄位，未知欄位回固定`422`。
- 成功只回傳sanitized structured fields、opaque report ID、`requiresHumanConfirmation=true`與`submissionStatus=local_draft_only`。不得回傳identity hash、idempotency key、payload fingerprint、cookie、token、DSN或raw exception。
- mutation必須驗證Player CSRF；401／403／409／422／429使用固定public error contract，不回顯敏感原文。

固定成功response只包含：

```json
{
  "reportId": "draft-0123456789abcdef",
  "category": "general_issue",
  "summary": "sanitized summary",
  "reproductionSteps": ["sanitized step"],
  "expectedBehavior": "待人工補充",
  "actualBehavior": "sanitized actual behavior",
  "requiresHumanConfirmation": true,
  "submissionStatus": "local_draft_only"
}
```

固定public error envelope為`{"error":{"code":"...","message":"..."}}`：

| HTTP | code | message |
| --- | --- | --- |
| 401 | `SESSION_NOT_FOUND` | `目前的遊戲工作階段已失效。` |
| 401 | `PLAYER_SESSION_REQUIRED` | `需要有效的玩家工作階段。` |
| 403 | `CSRF_FAILED` | `CSRF 驗證失敗。` |
| 409 | `SUPPORT_REPORT_CONFLICT` | `問題草稿狀態衝突，請重新整理後再試。` |
| 422 | `REQUEST_VALIDATION_FAILED` | `請檢查輸入內容。` |
| 429 | `SUPPORT_RATE_LIMITED` | `操作過於頻繁，請稍後再試。` |
| 500 | `SUPPORT_UNAVAILABLE` | `客服暫時無法使用，請稍後再試。` |

所有Support endpoint錯誤只能使用上述envelope與mapping，不得回FastAPI `detail`、raw validation、input或底層例外。

## Rate limit 與副作用

- 規則查詢與問題草稿各自有獨立、可測試的fixed-window limiter；規則查詢同一client source每60秒最多10次，問題草稿同一canonical Room／Player identity每10分鐘最多3次。兩者互不共用quota；時鐘由composition注入。
- Limiter不得在超限後呼叫Support model、knowledge base或repository。第一版不宣稱跨process／restart durability；production deploy前需依實際Web process數量再做release review。
- 相同authenticated identity與相同normalized description重送仍由既有repository收斂成同一草稿；divergent replay／collision維持fail closed。
- HTTP route固定intent：`rules:lookup`只能進入read-only rules use case，`reports:draft`只能進入local-draft use case；Support model output不得在兩者間切換route。

## Web contract

- UI明確分成「查詢遊戲規則」與「建立問題草稿」，不讓模型自行把匿名問題切換為寫入操作。
- Session capability固定沿用`GET /api/v1/rooms/current`（`credentials: include`），由`room.session`讀取`principalType`、`playerId`與`csrfToken`；只有`principalType="player"`且`csrfToken`非空才能建立草稿。Host若同時有Player cookie，既有`session_context`會回player且`isHost=true`，因此可用；純Host session不可代替Player。
- Draft adapter固定使用`credentials: include`與`X-CSRF-Token`，request body仍只有`description`。
- 規則答案顯示引用；unsupported顯示資料不足，不猜測。
- 問題草稿顯示「尚未提交、需要人工確認」，不提供外部送出按鈕。
- Loading、validation、401／403、429與safe generic error皆有可見且可由assistive technology讀取的狀態；不得顯示raw exception或runtime metadata。

## 平行 owner 與停止條件

- `codex/support-agent-api`擁有Python API、composition、R3 security tests、此Feature與validation evidence；不得修改Web、migration、AWS或external submit。
- `codex/support-agent-web`只擁有Support port／use case／HTTP adapter／page與專屬Web tests；不得修改Backend或本文件。
- API先整合；Web merge gate在最新main上驗證固定contract與完整Frontend regression。任一分支需要白名單外路徑、Bedrock、migration、外部傳輸或production deploy時立即停止並交回整合task。
