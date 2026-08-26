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
