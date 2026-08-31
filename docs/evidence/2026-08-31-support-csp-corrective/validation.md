# Support Agent CSP corrective 驗證

- 日期：2026-08-31
- 分支：`codex/support-csp-corrective`
- 風險等級：R2
- 範圍：移除 Web inline script 與 Google Fonts 外部載入，改由既有 module 處理 `file://` 提示並使用本機／系統 CJK 字型。

## Strict TDD

- Red `a6a748c`：新增 HTML 無 inline script、module 保留 `file://` 提示與 CSS 無第三方字型請求 contract；現行實作精確失敗 2 項。
- Green `cdd7ec8`：移除 inline script；`bootstrap.js` 接管提示；CSS 改用 `--font-sans`／`--font-serif` 系統字型堆疊。
- Guard `8889914`：固定 module 啟動時必須實際呼叫提示 guard。
- Sensitivity：暫時移除 `showServerRequiredNoticeForFileProtocol()` 呼叫後，目標測試精確以「module 啟動時必須實際執行」失敗；還原後通過。

## 驗證結果

- Production navigation targeted：6 passed。
- Frontend full regression：112 passed。
- Backend CSP／internet release gate：9 passed。
- Backend full regression：passed；僅既有 Starlette deprecation warning。
- `default-src 'self'` 未修改；未加入 `unsafe-inline`、nonce、hash或第三方字型來源。
- `git diff --check`：passed。
- Branch boundary：`branch_boundary=passed:codex/support-csp-corrective:paths=5`。

## Production 邊界

- 本分支未執行 AWS CLI、SSM、S3、Bedrock、`workflow_dispatch`或 production deploy。
- 合併後必須以新的 exact `main` SHA 與當前 active digest形成獨立 `digest-release`人工核准 envelope。
