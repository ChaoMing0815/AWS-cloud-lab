import test from "node:test";
import assert from "node:assert/strict";

let GenerateWorld;
try {
  ({ GenerateWorld } = await import("../../src/application/use-cases/generate-world.js"));
} catch {
  GenerateWorld = undefined;
}

test("GenerateWorld 正規化關鍵字並只透過 GameApi port 生成草稿", async () => {
  assert.equal(typeof GenerateWorld, "function", "GenerateWorld use case 尚未建立");
  let command;
  const expected = { status: "DRAFT", worldGenerationCount: 1 };
  const gameApi = {
    async generateWorld(received) {
      command = received;
      return expected;
    },
  };

  const result = await new GenerateWorld(gameApi).execute({
    keywords: " 夜班, 便利商店，盤點 ",
    tone: "mystery",
    customTone: " ",
    supplementalRequest: " 讓玩家先編輯。 ",
  });

  assert.equal(result, expected);
  assert.deepEqual(command, {
    keywords: ["夜班", "便利商店", "盤點"],
    tone: "mystery",
    customTone: null,
    supplementalRequest: "讓玩家先編輯。",
  });
  await assert.rejects(
    new GenerateWorld(gameApi).execute({ keywords: "只有,兩個", tone: "mystery" }),
    { code: "INVALID_WORLD_KEYWORDS" },
  );
  await assert.rejects(
    new GenerateWorld(gameApi).execute({
      keywords: "一,二,三",
      tone: "mystery",
      customTone: "不應提供",
    }),
    { code: "INVALID_CUSTOM_TONE" },
  );
});
