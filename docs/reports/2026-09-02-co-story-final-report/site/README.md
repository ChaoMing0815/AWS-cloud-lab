# 共演計劃期末報告網站

這是一份純本機、單一路由的 16:9 scrollytelling 報告。網站使用 repo-local AWS Architecture Icons、系統字型與靜態 HTML／CSS／JavaScript，執行時不需要外部網路。

## 啟動

可直接以 Chrome 開啟本目錄的 `index.html`；不需要安裝套件或啟動服務。若希望以 HTTP 預覽，在本目錄執行：

```bash
node scripts/serve.mjs
```

開啟 `http://127.0.0.1:4173/`。可使用滑鼠／觸控板捲動，也可使用 `ArrowUp`、`ArrowDown`、`PageUp`、`PageDown`、`Home` 與 `End` 導覽。

## 驗證

```bash
node --test tests/*.test.mjs
node scripts/build.mjs
node scripts/capture.mjs
```

固定截圖位於相鄰的 `captures/` 目錄；章節、順序與尺寸定義於 `capture-manifest.json`。網址加入 `?capture=1#章節-id` 可立即停駐在穩定畫面，架構演進章節另可使用 `architecture=classic|observable|componentized|current`。以 `?reduced=1#章節-id` 可檢查不含轉場的靜態版本。
