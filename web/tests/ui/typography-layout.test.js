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
