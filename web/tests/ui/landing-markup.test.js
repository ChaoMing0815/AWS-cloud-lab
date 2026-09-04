import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";


test("無 session 的根頁提供正式建立、加入與次要 Demo 入口，不呈現 Demo 房間", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");

  assert.match(html, /id=["']landingPage["']/, "缺少正式 Landing page");
  assert.match(html, /id=["']createGameForm["']/, "缺少建立遊戲入口");
  assert.match(html, /id=["']joinGameForm["']/, "缺少加入遊戲入口");
  assert.match(html, /id=["']joinGameButton["']/, "缺少加入送出按鈕");
  assert.match(html, /id=["']joinGameError["']/, "缺少加入錯誤訊息區");
  assert.match(html, /id=["']continueGamePanel["']/, "缺少繼續遊戲區塊");
  assert.match(html, /id=["']continueGameButton["']/, "缺少繼續遊戲按鈕");
  assert.match(html, /id=["']sessionNotice["']/, "缺少 session 狀態訊息");
  assert.match(html, /href=["']\/demo["']/, "缺少次要教學 Demo 入口");
  assert.match(html, /id=["']trialSafetyNotice["']/, "缺少公開試玩安全提醒");
  assert.match(html, /使用暱稱/);
  assert.match(html, /勿輸入.*個人資料.*機密/);
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


test("正式 Play 與 Ending deep link 會組裝遊戲頁", async () => {
  const bootstrap = await readFile(
    new URL("../../src/composition/bootstrap.js", import.meta.url),
    "utf8",
  );

  assert.match(bootstrap, /\/play/);
  assert.match(bootstrap, /\/ending/);
});


test("首頁以穩定 DOM hook 顯示中性的人工 release version 與同源可存取品牌圖示", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");

  assert.match(html, /id=["']releaseVersion["'][^>]*>Release v1\.1\.3</);
  assert.doesNotMatch(html, /Release v1\.1\.[01]|id=["']uiReleaseVersion["']|>UI v1\.1\.2</);
  assert.match(html, /<img[^>]+src=["']\/assets\/co-story-mark\.svg["'][^>]+alt=["']共演計劃品牌圖示["']/);
  assert.doesNotMatch(html, /class=["']brand-mark["'][^>]*>共</);
  const mark = await readFile(new URL("../../assets/co-story-mark.svg", import.meta.url), "utf8");
  assert.match(mark, /<title(?:\s+[^>]*)?>共演計劃品牌圖示<\/title>/);
  assert.doesNotMatch(mark, /(?:href|src)=["']https?:/i, "品牌 SVG 不得依賴外部資源");
});
