import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

test("DRAFT 房主世界表單提供生成草稿輸入、按鈕與剩餘次數", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");

  for (const id of [
    "worldKeywordsInput",
    "supplementalRequestInput",
    "generateWorldButton",
    "worldGenerationRemaining",
  ]) {
    assert.match(html, new RegExp(`id=["']${id}["']`), `缺少 #${id}`);
  }
  assert.match(html, /3[–-]5.*關鍵字|關鍵字.*3[–-]5/);
  assert.match(html, /補充要求/);
  assert.match(html, /生成世界草稿/);
  assert.match(html, /剩餘.*次/);
});
