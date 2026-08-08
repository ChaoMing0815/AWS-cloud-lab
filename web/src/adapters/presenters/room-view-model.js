export function toRoomViewModel(room) {
  const completed = room.players.filter(({ action, hasSubmitted }) => hasSubmitted ?? Boolean(action)).length;
  const playerTotal = room.players.length;
  return {
    roomCode: room.roomCode,
    roundLabel: String(room.round).padStart(2, "0"),
    playerCountLabel: `${playerTotal} / 5`,
    completed,
    progressLabel: `${completed} / ${playerTotal}`,
    progressPercent: playerTotal === 0 ? 0 : (completed / playerTotal) * 100,
    aiStatus: playerTotal < 3
      ? `至少還需要 ${3 - playerTotal} 位玩家才能開始回合。`
      : completed === playerTotal
        ? "所有玩家已提交，等待故事結算。"
        : `還有 ${playerTotal - completed} 位玩家尚未提交。`,
    world: room.world,
    currentPlayerId: room.session?.playerId ?? null,
    players: room.players.map((player) => ({
      ...player,
      hasSubmitted: player.hasSubmitted ?? Boolean(player.action),
      isActive: player.id === room.session?.playerId,
    })),
    entries: room.entries,
    canSubmitAction: room.session?.principalType === "player",
  };
}
