import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";


test("頁面提供正式進度、提前完成控制與結局區塊", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");

  for (const id of [
    "gameProgressBar",
    "dangerBar",
    "completionControls",
    "finishNowButton",
    "continueButton",
    "endingPanel",
    "endingResultText",
    "endingCostText",
  ]) {
    assert.match(html, new RegExp(`id=["']${id}["']`), `缺少 #${id}`);
  }
});
