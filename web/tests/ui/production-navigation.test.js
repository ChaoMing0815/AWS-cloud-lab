import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

test("直接以 file 開啟時頁面提供 server-required 提示，且 deep route 資產維持 root-relative", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");

  assert.match(html, /id=["']serverRequiredNotice["'][^>]*hidden/, "缺少預設隱藏的 #serverRequiredNotice");
  assert.match(
    html,
    /需由本機或正式 Web server 開啟/,
    "file:// 模式必須明確告知需由本機或正式 Web server 開啟",
  );
  assert.match(html, /href=["']\/styles\.css["']/, "deep route 的 stylesheet 必須維持 root-relative");
  assert.match(html, /src=["']\/runtime-config\.js["']/, "FastAPI shell 必須保留 runtime config");
  assert.match(html, /src=["']\/src\/composition\/bootstrap\.js["']/, "deep route 的 bootstrap 必須維持 root-relative");
});

test("index 內嵌啟動防線僅在 file:// 顯示 server-required 提示", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");

  assert.match(html, /location\.protocol\s*===\s*["']file:["']/);
  assert.match(html, /getElementById\(["']serverRequiredNotice["']\)/);
  assert.match(
    html,
    /if\s*\(\s*globalThis\.location\.protocol\s*===\s*["']file:["']\s*\)[\s\S]*serverRequiredNotice\.hidden\s*=\s*false/,
    "HTTP／HTTPS 不得移除預設 hidden",
  );
});

test("browser back／forward 的 popstate 會重新依 server canonical route 載入 shell", async () => {
  const bootstrap = await readFile(
    new URL("../../src/composition/bootstrap.js", import.meta.url),
    "utf8",
  );

  assert.match(
    bootstrap,
    /addEventListener\(\s*["']popstate["']\s*,\s*\(\)\s*=>\s*\{?\s*globalThis\.location\.reload\(\)/,
    "popstate 必須 reload，交回 FastAPI route shell 處理",
  );
});
