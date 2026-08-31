import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";


test("遊戲頁不顯示沒有 room-code rotation contract 的建立新房間控制", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");
  const gamePage = await readFile(
    new URL("../../src/ui/pages/game-page.js", import.meta.url),
    "utf8",
  );

  assert.doesNotMatch(html, /id=["']newRoomButton["']/);
  assert.doesNotMatch(gamePage, /byId\(["']newRoomButton["']\)/);
});
