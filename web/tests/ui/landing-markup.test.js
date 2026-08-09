import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";


test("無 session 的根頁提供正式建立、加入與次要 Demo 入口，不呈現 Demo 房間", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");

  assert.match(html, /id=["']landingPage["']/, "缺少正式 Landing page");
  assert.match(html, /id=["']createGameForm["']/, "缺少建立遊戲入口");
  assert.match(html, /id=["']joinGameForm["']/, "缺少加入遊戲入口");
  assert.match(html, /href=["']\/demo["']/, "缺少次要教學 Demo 入口");
  assert.doesNotMatch(html, /BONUS7/, "正式根頁不可硬編碼 Demo 房間");
});


test("進入教學 Demo 時 hidden Landing 不會繼續顯示", async () => {
  const css = await readFile(new URL("../../styles.css", import.meta.url), "utf8");

  assert.match(
    css,
    /\.landing-shell\[hidden\]\s*\{\s*display:\s*none;?\s*\}/,
    "Landing 的 layout rule 不可覆蓋 hidden 狀態",
  );
});
