import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";


test("responsive typography 避免標題與正文留下孤立短行", async () => {
  const css = await readFile(new URL("../../styles.css", import.meta.url), "utf8");
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");

  assert.match(
    css,
    /h1,\s*h2,\s*h3,\s*\.section-heading\s*\{[^}]*text-wrap:\s*balance/s,
  );
  assert.match(css, /p,\s*li\s*\{[^}]*text-wrap:\s*pretty/s);
  assert.doesNotMatch(html, /<h1>[^<]*<br\s*\/?\s*>/i);
});


test("production footer 的較長狀態文案可在窄螢幕安全換行", async () => {
  const css = await readFile(new URL("../../styles.css", import.meta.url), "utf8");

  assert.match(css, /footer\s*\{[^}]*flex-wrap:\s*wrap/s);
  assert.match(css, /footer\s*\{[^}]*gap:\s*[^;}]+/s);
});


test("列印或分頁時不留下單行孤頁並避免敘事卡片被拆開", async () => {
  const css = await readFile(new URL("../../styles.css", import.meta.url), "utf8");

  assert.match(css, /@media\s+print\s*\{/);
  assert.match(css, /h1,\s*h2,\s*h3\s*\{[^}]*break-after:\s*avoid-page/s);
  assert.match(css, /p,\s*li\s*\{[^}]*orphans:\s*2[^}]*widows:\s*2/s);
  assert.match(
    css,
    /\.entry-panel,\s*\.panel,\s*\.story-entry,\s*\.objective,\s*\.ai-card,\s*\.ending-panel\s*\{[^}]*break-inside:\s*avoid-page/s,
  );
});


test("終端敘事 token 只套用系統狀態與資料文字，故事正文維持 serif", async () => {
  const css = await readFile(new URL("../../styles.css", import.meta.url), "utf8");
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");

  assert.match(css, /--font-mono-system:\s*ui-monospace[^;]+;/s);
  assert.match(css, /\.terminal-log[^}]*font-family:\s*var\(--font-mono-system\)/s);
  assert.match(css, /\.room-code-row strong[^}]*font-family:\s*var\(--font-mono-system\)/s);
  assert.match(css, /\.dice-result[^}]*font-family:\s*var\(--font-mono-system\)/s);
  assert.match(css, /\.story-entry p[^}]*font-family:\s*var\(--font-serif\)/s);
  assert.match(html, /id=["']phaseStatus["'][^>]*class=["'][^"']*terminal-log/);
  assert.match(html, /class=["'][^"']*ai-label[^"']*["'][^>]*>&gt; AI 故事主持人</);
});


test("終端狀態在窄螢幕可換行且動態游標支援 reduced motion", async () => {
  const css = await readFile(new URL("../../styles.css", import.meta.url), "utf8");

  assert.match(css, /\.terminal-log[^}]*overflow-wrap:\s*anywhere/s);
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)[^{]*\{[\s\S]*\.terminal-cursor[^{]*\{[^}]*animation:\s*none/s);
  assert.match(css, /@media\s*\(max-width:\s*720px\)[^{]*\{[\s\S]*button[^}]*min-height:\s*44px/s);
});
