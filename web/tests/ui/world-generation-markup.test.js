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
    "worldGenerationFeedback",
  ]) {
    assert.match(html, new RegExp(`id=["']${id}["']`), `缺少 #${id}`);
  }
  assert.match(html, /3[–-]5.*關鍵字|關鍵字.*3[–-]5/);
  assert.match(html, /補充要求/);
  assert.match(html, /生成世界草稿/);
  assert.match(html, /剩餘.*次/);
  assert.match(html, /id=["']worldGenerationFeedback["'][^>]*aria-live=["']assertive["']/);
});

test("公開試玩文案使用泛用行動範例並標示 AWS Bedrock 部署", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");
  const bootstrap = await readFile(
    new URL("../../src/composition/bootstrap.js", import.meta.url),
    "utf8",
  );

  assert.doesNotMatch(html, /三個部門的資料整合/);
  assert.match(html, /描述角色想做什麼、如何做，以及希望達成的效果/);
  assert.doesNotMatch(html, /AWS 部署尚未執行/);
  assert.match(html, /AWS Tier 0 公開試玩/);
  assert.match(html, /Amazon Bedrock/);
  assert.doesNotMatch(bootstrap, /本機 FastAPI 模式|本機原型/);
  assert.match(bootstrap, /AWS 公開試玩/);
  assert.match(bootstrap, /private PostgreSQL/);
});

test("DRAFT 世界表單為可由 API 標示的欄位提供錯誤訊息區", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");

  for (const id of [
    "worldTitleError",
    "worldPremiseError",
    "worldObjectiveError",
    "openingSceneError",
    "coreObstacleError",
  ]) {
    assert.match(html, new RegExp(`id=["']${id}["']`), `缺少 #${id}`);
  }
  assert.match(html, /aria-describedby=["']worldPremiseError["']/);
});
