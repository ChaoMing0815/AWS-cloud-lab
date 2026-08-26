# Storyteller 因果敘事品質

- 狀態：Implemented
- 風險：R2（LLM adapter 與可觀察故事輸出）
- 上游：正式 MVP Spec 第 11–13、20 節
- 非目標：不擴張世界觀生成、不修改骰點／進度／危機／結局規則、不呼叫真實 Bedrock

## 可觀察 contract

1. 每回合敘事承接最近已提交場景，不把玩家 action 當成前一幕，也不重置時間線。
2. 每位已結算玩家各有角色、具體 action、行動方式、完整骰點與固定成功等級 context。
3. 成功、部分成功與失敗分別形成突破、帶代價的進展與 fail-forward 障礙。
4. 規則引擎提供的進度／危機 delta 會成為具體事件後果；Storyteller 不重算或修改 canonical state。
5. 下一場景必須由本回合後果自然形成。
6. 結局承接最後事件，將固定結果與代價轉成成果、犧牲及未解後果。
7. 模型只取得最近五筆 narrator／ending 事件，避免 prompt history 無界增長。

## 實作邊界

- `BedrockStoryteller` 固定 guarded prompt shape 與 narrative requirements；仍保留 1,200 字元輸出上限及既有 recovery taxonomy。
- `MockStoryteller` 以 deterministic 模板呈現同一批 canonical input，讓本機與測試可重現。
- Web 已按 append-only story entry 顯示後端敘事，本切片不需要新增 UI state 或 client-side 規則。

## Forced-tool structured contract

- `resolve_round_narrative` 只能呼叫 `submit_round_narrative`，欄位固定為共同敘事、逐玩家 action consequence、進度後果、危機後果與下一幕 hook。
- 結局只能呼叫 `submit_ending_narrative`，欄位固定為結局敘事、達成成果、付出代價／犧牲與未解後果。
- 每次 Converse request 只提供一個 output-only tool，使用指定 tool choice 與 `strict=true`；不提供 recovery、state mutation 或其他 side-effect tool。
- Adapter 只接受單一 `toolUse` content block、正確 tool name、完整且無額外欄位的 input；round 的 player ID 必須恰好等於 canonical 已結算玩家集合。
- 純文字 JSON、額外 text／tool block、錯誤 tool、缺欄位、額外欄位、重複或未知玩家均映射為安全 `SCHEMA_INVALID`，不洩漏 raw model content。
- 驗證後由 adapter 依固定順序組成既有 `Storyteller -> str` output；不修改 port、domain 或 game engine state authority。
- 世界觀生成維持既有 text JSON contract，不取得 narrative tool config。
