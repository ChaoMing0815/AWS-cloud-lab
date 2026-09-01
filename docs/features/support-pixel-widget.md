# 像素 Support Agent Widget

- 狀態：Production verified（2026-09-01）；`codex/support-pixel-widget`僅為已完成歷史分支，不得續作
- 上游：`docs/features/support-agent-integration.md`、ADR-0005
- 風險：R2 可觀察 UX
- 共同治理基準：`3152a9bc59c284850570ee0ee16ba0964a8966d4`
- Production source：`1297a6acabaf30ca4ec2205e7641b7ab83cef781`
- Active Web digest：`sha256:5a10597d473cd21c5b2754b743f4a48de2be7cae9bd0c1816c535523284df9bd`
- Canonical production evidence：[`2026-09-01-ui-support-production-release`](../evidence/2026-09-01-ui-support-production-release/validation.md)

## 目標

在不離開當前頁面與不改變遊戲狀態的前提下，以全站可收合的純 CSS 像素史萊姆開關，包裝已部署的 bounded Support Agent。`/support` 完整頁繼續保留。

## 固定功能與安全語意

- 「查規則」是匿名、read-only 的 cited／unsupported 查詢；沒有規則來源時明確不猜測。
- 「建草稿」只在 canonical Room 回傳有效 Player session 與 CSRF token 後啟用。
- 草稿成功固定顯示「尚未提交／需人工確認／不會對外提交」與 `local_draft_only`。
- Widget 明確說明不是自由對話 AI；不增加 route switching、Bedrock、RAG、MCP 或 external submit。

## 互動與 responsive contract

- Bootstrap 以 root-relative `/support-widget.css` 載入同源樣式；角色為純 CSS，無外部 asset、字型、CDN 或 dependency。
- 可見開關使用 `aria-expanded`，面板使用 non-modal `dialog` 語意；開啟後 focus 進入關閉鍵。
- `Esc` 或關閉鍵收合後將 focus 送回開關；兩種 intent、表單與完整頁連結均可以鍵盤操作。
- Loading、supported、unsupported、草稿成功與錯誤透過 `aria-live="polite"` status 呈現。
- `prefers-reduced-motion: reduce` 停用史萊姆動畫；720px 以下由頂部展開且可收合，保留下方遊戲 composer／control 區。

## 未納入

原分支切片不修改 `index.html`、全站 `styles.css`、遊戲頁、Backend／API／資料模型、Docker／workflow／ops／AWS；production deploy由整合task以既有Tier 3 pipeline另行完成，沒有擴張上述產品與安全邊界。
