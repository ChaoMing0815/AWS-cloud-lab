# Research：如何建立 LLM 多人文字 RPG

> 架構更正（2026-08-07）：本文件中的 DynamoDB 是早期候選設計，不是目前已接受的 AWS 資料層。產品與 LLM 研究仍可沿用；AWS repository 需等待 PostgreSQL／RDS ADR，且所有資料存取維持在 repository interface 後。

- 研究日期：2026-08-07
- 專題：共演計劃，多人 AI 協作故事遊戲
- 研究範圍：3–5 人、回合制、純文字、AWS 可部署 MVP
- 狀態：研究完成；grill-me 訪談已確認，正式需求見 [MVP Spec](../specs/text-rpg-mvp-spec.md)

## 1. 核心結論

LLM 最適合擔任「理解玩家自由文字、提出結果、生成敘事」的故事主持人，不應成為遊戲狀態的唯一真實來源。伺服器必須保存可驗證的 canonical state，並決定哪些狀態更新可以提交。

推薦的 MVP 回合流程：

```text
收集所有玩家行動
  → 驗證房間、玩家、回合與輸入
  → 組合世界規則、canonical state、近期事件與玩家行動
  → 呼叫一次 LLM
  → 取得符合 schema 的敘事與 state-delta proposal
  → 應用程式驗證並套用允許的狀態變更
  → 原子保存事件、新狀態與玩家可見敘事
  → 開始下一回合
```

這個設計保留自由輸入與生成式敘事，同時避免 LLM 自行創造不存在的道具、覆寫角色狀態、跳過回合或忘記先前事件。

## 2. 研究依據

### 2.1 LLM 能創作，但不可靠地維護長期規則

RPGBench 將 LLM 文字 RPG 分成遊戲建立與多回合模擬，並以結構化 event-state representation 驗證規則與狀態。研究結果指出，先進模型可以產生有趣故事，但在長或複雜情境中仍常無法維持可驗證的遊戲機制。[RPGBench](https://arxiv.org/abs/2502.00595)

Google Research 也把 RPG 視為「下一段對話生成＋從歷史預測遊戲狀態」的雙重問題；研究特別檢查 state tracking 是否能改善合理且有趣的輸出。[Dungeons and Dragons as a Challenge Problem for Artificial Intelligence](https://research.google/pubs/dungeons-and-dragons-as-a-challenge-problem-for-artificial-intelligence/)

設計影響：

- 故事文字不是 canonical state。
- 狀態必須以結構化資料保存。
- 每回合同時測試敘事品質與狀態正確性。

### 2.2 Function calling／structured output 能提升一致性

AI Game Master 研究顯示，加入骰子與狀態操作函式後，敘事品質、遊戲體驗與狀態一致性優於只靠自然語言 prompt。函式分為不直接修改狀態的隨機／判定函式，以及真正修改 inventory、NPC 等資料的 state functions。[Enhancing AI Game Masters with Function Calling](https://arxiv.org/abs/2409.06949)

Amazon Bedrock Structured Outputs 可要求模型輸出符合 JSON Schema 的結果，降低解析失敗與重試；strict tool use 也能限制工具名稱與參數格式。[Bedrock Structured Outputs](https://docs.aws.amazon.com/bedrock/latest/userguide/structured-output.html)

MVP 建議：

- 一個 LLM invocation 處理一個完整回合，而不是每位玩家各呼叫一次。
- 回傳 `narration`、`player_outcomes`、`state_delta_proposal`、`next_objective` 等固定欄位。
- 應用程式驗證 proposal；LLM 不直接寫入 DynamoDB。
- 若選定模型不支援 Structured Outputs，仍以 JSON prompt＋application validation＋最多一次修復重試處理。

### 2.3 記憶應分層，而不是重送完整聊天紀錄

Generative Agents 的研究架構將 observation、reflection、planning 存入 memory stream，再依 recency、importance 與 relevance 取回相關記憶，支持較一致的長期行為。[Generative Agents](https://arxiv.org/abs/2304.03442)

MVP 不需要完整 Agent memory 系統，但應保留五層上下文：

1. `world_rules`：固定世界觀、語氣、安全與遊戲規則。
2. `canonical_state`：房間、玩家、角色、場景、目標、物品與旗標。
3. `recent_events`：最近 3–5 回合的結構化事件與敘事。
4. `story_summary`：較早劇情的壓縮摘要。
5. `current_actions`：本回合所有玩家原始行動。

長期事件不能只存在摘要中；摘要是 prompt context，event log 才是稽核與重新生成依據。

### 2.4 多人回合需要明確狀態機

多人版本的主要難題不是生成文字，而是確保每位玩家只對正確回合提交一次行動，且同一回合不被重複解析。

推薦房間狀態：

```text
LOBBY
  → COLLECTING_ACTIONS
  → RESOLVING
  → REVEALING
  → COLLECTING_ACTIONS（下一回合）
  → COMPLETED
```

必要約束：

- `room_id + round_number + player_id` 唯一識別一次行動。
- 只有 `COLLECTING_ACTIONS` 可以提交。
- 只有房主或「所有玩家已提交」事件可以開始解析。
- `RESOLVING` 使用版本號或 conditional write 防止重複 LLM invocation。
- 儲存 LLM request ID、model ID、token usage、latency 與結果狀態，但不保存憑證。
- Timeout、玩家離線、修改行動與房主強制推進的規則必須在 Spec 決定。

### 2.5 Prompt 應是資料合約，不只是角色扮演指令

Amazon Bedrock Prompt management 支援變數、版本與 variant 比較；Converse API 可統一多模型對話格式，也能搭配 prompt caching。[Prompt management](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-management.html)、[Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)

建議 prompt 區塊：

```text
SYSTEM CONTRACT
SAFETY AND IP RULES
WORLD RULES
CANONICAL STATE
STORY SUMMARY
RECENT EVENTS
UNTRUSTED PLAYER ACTIONS
OUTPUT SCHEMA
```

玩家行動必須標示為 untrusted data，不能讓「忽略規則」「顯示 system prompt」「替自己增加道具」等文字覆蓋 system contract。

### 2.6 安全不是最後才加的功能

AWS 建議以輸入驗證、模型內建防護、Bedrock Guardrails、prompt 邊界與輸出後處理形成多層防護，而不是只依靠單一 system prompt。[AWS Prompt Injection Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/llm-prompt-engineering-best-practices/llm-prompt-engineering-best-practices.html)、[Bedrock Guardrails with Converse](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-converse-api.html)

MVP 安全邊界：

- 玩家行動長度限制與 control-character 清理。
- 將每位玩家輸入放入明確資料欄位，不直接串接 prompt 指令。
- 不讓 LLM 呼叫任意 AWS、shell、網路或資料庫工具。
- 限定可接受的 state delta 欄位與值。
- 對輸入與輸出設定內容政策；政策強度由 Spec 決定。
- 不記錄完整個資、憑證或未遮蔽的敏感內容。

## 3. 建議的 MVP 領域模型

| Entity | 最小必要欄位 |
| --- | --- |
| Room | `room_id`、`join_code`、`host_player_id`、`status`、`round_number`、`version` |
| World | `title`、`premise`、`tone`、`rules`、`current_scene`、`objective` |
| Player | `player_id`、`nickname`、`joined_at`、`connection_status` |
| Character | `character_id`、`player_id`、`name`、`background`、`trait`、`weakness`、`courage`、`insight`、`bond`、`spark` |
| Action | `room_id`、`round_number`、`player_id`、`text`、`submitted_at`、`revision` |
| Turn | `round_number`、`status`、`started_at`、`resolved_at`、`model_id`、`usage` |
| Event | `event_id`、`type`、`visibility`、`payload`、`created_at` |
| StoryEntry | `round_number`、`narration`、`summary_delta`、`created_at` |

本表是研究階段的建議；已確認欄位與約束以正式 MVP Spec 為準。

## 4. 建議的 LLM 輸出合約

```json
{
  "narration": "玩家可見的本回合結果",
  "player_outcomes": [
    {
      "player_id": "string",
      "summary": "該玩家行動如何影響場景",
      "result": "success | partial | failure"
    }
  ],
  "state_delta_proposal": {
    "scene": "string or null",
    "objective": "string or null",
    "flags_to_add": ["string"],
    "inventory_changes": []
  },
  "story_summary_delta": "供長期摘要合併的短句",
  "next_prompt": "下一回合給玩家的情境或問題",
  "game_over": false
}
```

應用程式必須拒絕未知欄位、不存在的 player ID、未允許的物品、過長文字與不合法狀態轉換。

## 5. 模型與成本策略

- 使用 Amazon Bedrock On-Demand，不使用 Provisioned Throughput。
- MVP 優先測試低成本文字模型；模型最終選擇需以繁體中文敘事品質、schema adherence、延遲與 Tokyo 可用性實測決定。
- 每回合一次生成，避免每位玩家、NPC 或 Agent 各自呼叫模型。
- 只傳 canonical state、摘要、最近回合與當前行動，不傳完整歷史。
- 設定最大輸入／輸出 token 與 invocation timeout。
- 對相同 `room_id + round_number + state_version` 設定 idempotency，避免 retry 重複計費。
- Prompt caching 只有在靜態世界規則足夠長、模型支援且實測有節省時才啟用。[Bedrock Prompt Caching](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)

## 6. 驗收與評估方法

研究顯示，RPG 引擎需要同時評估客觀機制與主觀敘事；只看「文字很好看」不足以驗收。

### 客觀測試

- 每位玩家每回合最多一個有效 action。
- 同一回合最多一次成功 resolution。
- 不存在的 player／item／flag 不會被寫入。
- 狀態更新符合 schema 與允許的 transition。
- 重試不會重複扣道具或推進兩次。
- 重新載入後 canonical state、event log 與故事一致。

### 敘事評估

- 是否回應所有玩家的行動。
- 是否維持世界觀、角色與時間線一致。
- 是否給玩家有意義的影響，而非永遠成功或完全 railroad。
- 是否清楚描述成功、部分成功或失敗的後果。
- 是否避免抄用受保護世界觀與專有內容。
- 是否符合內容安全政策。

### 維運指標

- 每回合 end-to-end latency。
- LLM input／output token。
- 每回合估計成本。
- schema validation failure 與 retry 次數。
- Guardrail intervention 次數。
- HTTP error、DynamoDB conditional failure 與 resolution timeout。

## 7. MVP 不建議做的事

- 不做每個 NPC 一個 Agent 的多 Agent 系統。
- 不做完整規則書、技能樹、裝備經濟與戰鬥模擬器。
- 不讓 LLM 直接存取 AWS API、shell 或 DynamoDB。
- 不用完整聊天紀錄充當唯一記憶。
- 不做 WebSocket、配對、大廳聊天與社群帳號。
- 不在模型尚未評估前承諾特定 Bedrock model。
- 不因 Structured Outputs 可用就省略 application-side validation。

## 8. grill-me 決策結果

以下產品決策已由使用者逐項確認：

1. 以 3–5 人協作敘事與輕規則冒險為核心。
2. 世界可由房主直接輸入，或以關鍵字生成後編輯確認。
3. MVP 採 4／6／8 回合硬上限；不限回合隱藏關鍵字模式延後。
4. 角色不設職業或預設職能，由玩家自由描述。
5. 玩家將 3 點分配至勇氣、洞察、羈絆，每項上限 2。
6. 每個行動由玩家指定使用屬性，後端以 `2d6 + 屬性` 判定。
7. 星火初始 1、上限 3，可在看到骰子後花費 1 點使結果 `+1`。
8. 行動在結算前隱藏且可修改；房主手動開始結算或略過缺席者。
9. 成功／部分成功／失敗分別更新固定的進度與危機點數。
10. 進度達 100% 可提前結束或繼續；回合耗盡時依進度產生三類結局。
11. 固定五種故事調性、13+ 安全底線與原創內容要求。
12. 使用 room code、暱稱與安全 session cookie，不建立永久帳號。
13. LLM timeout 後自動重試一次，仍失敗則由房主重試或使用 fallback。
14. 房間最後活動 7 天後清理；logs 不保存完整故事、prompt 或 session token。
15. 以本機核心流程、自動測試、AWS 延後驗收關卡與 5–8 分鐘 Demo 定義完成。

訪談方法參考 [grill-me](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) 與其 [grilling 工作流](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)。完整欄位、公式、狀態機、API、安全與驗收條件以正式 [MVP Spec](../specs/text-rpg-mvp-spec.md) 為準。
