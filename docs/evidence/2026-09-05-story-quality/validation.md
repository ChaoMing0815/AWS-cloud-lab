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
- PR／merge：PR #85；PR CI run `34005023612`與main CI run `34005127848`均全綠，exact merge／application source為`415c5d32c46c82a39933031b81d5aca7939bd0c6`。
- Web production：run `34005215520`以previous `sha256:bda7bbbb3a071d83d68dafd4fecba06132407d6f6e644a1e4f9aaac0acb93bbb`完成OIDC、ARM64 immutable push、exact-digest Trivy與bounded SSM；active digest為`sha256:e4039cbf5e1b42b6dd0b8c63642b1a0302078ae59030aa23ce194c5ff3f04d30`。Strict TLS首頁／live／ready皆為`200`，首頁顯示`Release v1.1.4`。
- Worker production：run `34005216367`因同一SHA tag已由Web run建立而在ECR immutable fence安全停止，未掃描、未產生manifest且未修改runtime。由於Web run使用相同完整Docker image並已掃描exact digest，使用者透過SSM逐台將`ip-10-20-20-170`與`ip-10-20-20-91`更新至`sha256:e4039cbf…`；兩台均驗證source `415c5d32…`、service enabled／active、container running、restart `0`、async、tokens `3000`，專案registry與臨時credential absent。
- Rollback：Web回`sha256:bda7bbbb…`；兩台Worker回`sha256:439059c4…`並維持tokens `3000`。
- Residual：本次未呼叫Bedrock或建立story job；production敘事連續性仍需以一個bounded回合觀察。Web／Worker workflow共用immutable SHA tag造成第二條artifact workflow安全失敗，應另以TDD修正成驗證並重用既有exact digest。
