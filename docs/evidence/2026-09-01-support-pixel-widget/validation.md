# 像素 Support Agent Widget 驗證摘要

> 本文件保存功能分支TDD與本機QA；production現況以[`2026-09-01-ui-support-production-release`](../2026-09-01-ui-support-production-release/validation.md)為準。此分支已完成且不得續作。

- Scope／risk／upstream：全站 bounded Support Widget，R2；Support Integration Contract 與 ADR-0005。
- Base：`3152a9bc59c284850570ee0ee16ba0964a8966d4`；branch `codex/support-pixel-widget`。
- Baseline：Frontend `113 passed`。
- Red commit：`64feb34` 對全站掛載、intent、a11y、安全語意與 responsive 建立 6 項失敗測試。
- Green commit：`ef483ea` 加入純 CSS 像素 Widget、同源 stylesheet 與既有 Support use case 組合。
- Mobile Red：`faa49ef` 證明 720px 以下仍缺少頂部展開約束。
- Mobile Green：`dccd9b4` 將手機 Widget 移至頂部，保留下方 composer／control 區。
- Targeted：`support-widget`、`support-page`、`production-navigation` 共 `17 passed`。
- Full Frontend：`119 passed`，`0 failed`。
- Browser QA：桌機開啟後 focus 為 close，Esc 關閉後回 toggle；匿名草稿為 disabled。
- Mobile QA：390×844 的 dialog `top=72`、`bottom=513`，無水平溢位，三重草稿安全文案可見。
- Negative：無外部 URL／asset／dependency；unsupported 不顯示 citation 且明確不猜測。
- Rollback：cherry-pick 時可整體 revert 本分支 commits；未修改 API、schema 或 production state。
- Residual risk：`/support` 完整頁與 Widget 各自讀取 canonical session，因此該路徑會有兩次 read-only current-room request。
