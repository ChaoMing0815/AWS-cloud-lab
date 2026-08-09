import test from "node:test";
import assert from "node:assert/strict";

let JoinRoomByCode;
try {
  ({ JoinRoomByCode } = await import("../../src/application/use-cases/join-room-by-code.js"));
} catch {
  JoinRoomByCode = undefined;
}

test("JoinRoomByCode 正規化六碼房號與暱稱", async () => {
  assert.equal(typeof JoinRoomByCode, "function", "JoinRoomByCode 尚未建立");
  const commands = [];
  const useCase = new JoinRoomByCode({
    async joinRoomByCode(command) {
      commands.push(command);
      return { roomCode: command.roomCode };
    },
  });

  await useCase.execute({ roomCode: " abcd23 ", nickname: " 小明 " });

  assert.deepEqual(commands, [{ roomCode: "ABCD23", nickname: "小明" }]);
});

test("JoinRoomByCode 在送出前拒絕無效房號", () => {
  assert.equal(typeof JoinRoomByCode, "function", "JoinRoomByCode 尚未建立");
  const useCase = new JoinRoomByCode({ joinRoomByCode() {} });

  assert.throws(
    () => useCase.execute({ roomCode: "ABC", nickname: "小明" }),
    { code: "ROOM_CODE_INVALID" },
  );
});
