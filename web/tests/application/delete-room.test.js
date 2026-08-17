import test from "node:test";
import assert from "node:assert/strict";

let DeleteRoom;
try {
  ({ DeleteRoom } = await import("../../src/application/use-cases/delete-room.js"));
} catch {
  DeleteRoom = undefined;
}

test("DeleteRoom 只透過 GameApi port 執行永久刪除", async () => {
  assert.equal(typeof DeleteRoom, "function", "DeleteRoom use case 尚未建立");
  let calls = 0;
  const expected = { deleted: true };
  const gameApi = {
    async deleteRoom() {
      calls += 1;
      return expected;
    },
  };

  const result = await new DeleteRoom(gameApi).execute();

  assert.equal(result, expected);
  assert.equal(calls, 1);
});
