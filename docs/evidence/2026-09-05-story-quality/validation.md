# 故事連續性與閱讀位置修正驗證摘要

- Scope：後續回合不重述固定開場、不重複精確相同的後果段落，並保留玩家主動上捲的故事位置。
- Risk：R2，橫跨 Bedrock 敘事 adapter 與玩家可見 Web polling 體驗。
- Upstream：使用者 2026-09-05 production 遊玩觀察；不修改遊戲規則、固定骰點或 canonical state。
- Baseline：Bedrock targeted `79/79`；Frontend targeted `18/18`。
- Red：`9faaac2`，已確認固定開場、強制滾底與舊版號三類期待失敗。
- Green：`c7c8016`，排除敘事 prompt 的固定開場、加入精確去重，並以距底閾值決定是否自動跟隨。
- Version：玩家可見版號由 `Release v1.1.3` 遞增為 `Release v1.1.4`。
- Targeted：Bedrock `80/80`；Frontend `20/20`。
- Full regression：Backend 全套 exit `0`；Frontend `132/132`。
- Browser QA：本機 `/demo` 顯示 v1.1.4、水平溢位 `0`、console error／warn `0`。
- Browser 限制：Demo fixture 只有兩筆故事，未產生真實滾動高度；長紀錄位置由 DOM 行為測試驗證。
- Boundary：`branch_boundary=passed:codex/story-quality:paths=7`。
- Residual：本機不呼叫 Bedrock；production 敘事品質仍需在新 release 後以一個 bounded 回合觀察。
