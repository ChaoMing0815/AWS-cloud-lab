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

test("既有 module 在 file:// 顯示 server-required 提示，且 HTML 不含 inline script", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");
  const bootstrap = await readFile(
    new URL("../../src/composition/bootstrap.js", import.meta.url),
    "utf8",
  );

  assert.doesNotMatch(
    html,
    /<script(?![^>]*\bsrc\s*=)[^>]*>[\s\S]*?<\/script>/i,
    "CSP default-src 'self' 下不得保留 inline script",
  );
  assert.match(bootstrap, /location\.protocol\s*===\s*["']file:["']/);
  assert.match(bootstrap, /getElementById\(["']serverRequiredNotice["']\)/);
  assert.match(
    bootstrap,
    /if\s*\(\s*globalThis\.location\.protocol\s*===\s*["']file:["']\s*\)[\s\S]*serverRequiredNotice\.hidden\s*=\s*false/,
    "HTTP／HTTPS 不得移除預設 hidden",
  );
});

test("Web 樣式只使用本機或系統 CJK 字型，不載入 Google Fonts", async () => {
  const css = await readFile(new URL("../../styles.css", import.meta.url), "utf8");

  assert.doesNotMatch(css, /@import\s+url\(/i);
  assert.doesNotMatch(css, /fonts\.(?:googleapis|gstatic)\.com/i);
  assert.match(css, /--font-sans:[^;]*system-ui[^;]*"PingFang TC"[^;]*"Microsoft JhengHei"[^;]*sans-serif/);
  assert.match(css, /--font-serif:[^;]*"Songti TC"[^;]*"Noto Serif TC"[^;]*serif/);
  assert.match(css, /font-family:\s*var\(--font-sans\)/);
  assert.match(css, /font-family:\s*var\(--font-serif\)/);
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

test("deep route 在 canonical room 載入完成前只顯示安全 loading shell", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");
  const bootstrap = await readFile(
    new URL("../../src/composition/bootstrap.js", import.meta.url),
    "utf8",
  );

  assert.match(html, /id=["']appLoadingStatus["'][^>]*role=["']status["']/);
  assert.match(html, /id=["']landingPage["'][^>]*hidden/);
  assert.match(bootstrap, /async function mountGamePage/);
  assert.match(bootstrap, /await page\.mount\(\)[\s\S]*showSurface\(["']gamePage["']\)/);
  assert.match(bootstrap, /showLoading\(\)[\s\S]*await page\.mount\(\)/);
});

test("遊戲規則頁有獨立路徑、返回首頁與核心規則摘要", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");
  const bootstrap = await readFile(
    new URL("../../src/composition/bootstrap.js", import.meta.url),
    "utf8",
  );

  assert.match(html, /href=["']\/rules["'][^>]*>遊戲規則/);
  assert.match(html, /id=["']rulesPage["']/);
  assert.match(html, /回合怎麼進行/);
  assert.match(html, /2d6 \+ 屬性/);
  assert.match(html, /星火/);
  assert.match(html, /href=["']\/["'][^>]*>返回首頁/);
  assert.match(bootstrap, /path === ["']\/rules["']/);
});
