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
- `supported`回傳canonical answer與至少一筆`ruleId`、`title`、`sourceSection`、`sourceVersion`引用。
- `unsupported`使用既有固定回答且citations為空；不得由API或UI補寫規則。

### 問題草稿

```http
POST /api/v1/support/reports:draft
Content-Type: application/json
X-CSRF-Token: <player csrf>

{"description":"重現步驟與預期／實際結果"}
```

- 必須有有效current Room與Player session；房主以其Player session建立草稿，Host session本身不代替Player identity。
- `description`正規化後為1–2000字元。Reporter identity只由server以canonical room ID＋player ID衍生；request不得接受player ID、identity hash、report ID、submission state或human-confirmation flag。
- 成功只回傳sanitized structured fields、opaque report ID、`requiresHumanConfirmation=true`與`submissionStatus=local_draft_only`。不得回傳identity hash、idempotency key、payload fingerprint、cookie、token、DSN或raw exception。
- mutation必須驗證Player CSRF；401／403／409／422／429使用固定public error contract，不回顯敏感原文。

## Rate limit 與副作用

- 規則查詢與問題草稿各自有獨立、可測試的bounded limiter；同一process內同一來源超限回`429`並附固定retry提示。
- Limiter不得在超限後呼叫Support model、knowledge base或repository。第一版不宣稱跨process／restart durability；production deploy前需依實際Web process數量再做release review。
- 相同authenticated identity與相同normalized description重送仍由既有repository收斂成同一草稿；divergent replay／collision維持fail closed。

## Web contract

- UI明確分成「查詢遊戲規則」與「建立問題草稿」，不讓模型自行把匿名問題切換為寫入操作。
- 規則答案顯示引用；unsupported顯示資料不足，不猜測。
- 問題草稿顯示「尚未提交、需要人工確認」，不提供外部送出按鈕。
- Loading、validation、401／403、429與safe generic error皆有可見且可由assistive technology讀取的狀態；不得顯示raw exception或runtime metadata。

## 平行 owner 與停止條件

- `codex/support-agent-api`擁有Python API、composition、R3 security tests、此Feature與validation evidence；不得修改Web、migration、AWS或external submit。
- `codex/support-agent-web`只擁有Support port／use case／HTTP adapter／page與專屬Web tests；不得修改Backend或本文件。
- API先整合；Web merge gate在最新main上驗證固定contract與完整Frontend regression。任一分支需要白名單外路徑、Bedrock、migration、外部傳輸或production deploy時立即停止並交回整合task。
