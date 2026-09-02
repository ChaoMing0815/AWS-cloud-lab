# UI 終端敘事改版驗證摘要

- 狀態：Production verified（2026-09-01）
- Production source：`1297a6acabaf30ca4ec2205e7641b7ab83cef781`
- Active Web digest：`sha256:5a10597d473cd21c5b2754b743f4a48de2be7cae9bd0c1816c535523284df9bd`
- Canonical production evidence：[`2026-09-01-ui-support-production-release`](../evidence/2026-09-01-ui-support-production-release/validation.md)

- Scope／risk／upstream source：R2 可觀察 UX；共同基準 `3152a9bc59c284850570ee0ee16ba0964a8966d4`、branch policy 與正式產品邊界。
- 首頁版本：玩家可見且具穩定 `releaseVersion` DOM id 的中性人工版本 `Release v1.1.0`；不綁定單一改版類型，也不宣稱為 Git SHA。
- 品牌資產：新增同源 `co-story-mark.svg`，具可存取名稱且沒有外部資源。
- 視覺範圍：系統狀態、AI 標籤、房號與骰點採 system monospace；故事正文維持 serif。
- 狀態語意：一般狀態使用 `>`，錯誤／離線使用 `!`；`RESOLVING` 顯示實際已等待秒數。
- 非同步安全：超過 60 秒明示不會自動取消或重送；未新增 mutation、retry、cancel 或 fallback。
- 動效降級：只保留不承載內容的游標動畫，`prefers-reduced-motion` 時停用；未做逐字動畫。
- Baseline：完整 Frontend `113 passed`；首次 `npm` 不在 PATH，改用工作區隨附 Node.js runtime。
- Red commit：`110a414`；targeted `18 passed／5 failed`，失敗皆為缺少目標 UI 行為的 assertion。
- Green targeted：`23 passed／0 failed`。
- Full regression：`117 passed／0 failed`。
- Residual risk：未執行真實 screen reader 驗證，因此敘事正文維持靜態，不採逐字 reveal。
