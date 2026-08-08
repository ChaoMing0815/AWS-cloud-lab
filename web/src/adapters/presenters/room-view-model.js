export function toRoomViewModel(room) {
  const completed = room.players.filter(({ action, hasSubmitted }) => hasSubmitted ?? Boolean(action)).length;
  const playerTotal = room.players.length;
  const readyTotal = room.players.filter((player) => player.characterReady).length;
  return {
    roomCode: room.roomCode,
    roundLabel: String(room.round).padStart(2, "0"),
    playerCountLabel: `${playerTotal} / 5`,
    completed,
    progressLabel: `${completed} / ${playerTotal}`,
    progressPercent: playerTotal === 0 ? 0 : (completed / playerTotal) * 100,
    aiStatus: room.status === "DRAFT"
      ? "等待房主確認世界設定。"
      : room.status === "LOBBY"
        ? playerTotal < 3
          ? `至少還需要 ${3 - playerTotal} 位玩家才能開始。`
          : "人數已足夠，等待房主開始遊戲。"
        : completed === playerTotal
          ? "所有玩家已提交，等待故事結算。"
          : `還有 ${playerTotal - completed} 位玩家尚未提交。`,
    world: room.world,
    currentPlayerId: room.session?.playerId ?? null,
    players: room.players.map((player) => ({
      ...player,
      role: player.character?.name ?? player.role,
      characterReady: Boolean(player.characterReady),
      hasSubmitted: player.hasSubmitted ?? Boolean(player.action),
      isActive: player.id === room.session?.playerId,
    })),
    entries: room.entries,
    status: room.status,
    maxRounds: room.maxRounds,
    isHost: Boolean(room.session?.isHost),
    canEditWorld: Boolean(room.session?.isHost) && room.status === "DRAFT",
    canJoin: room.status === "LOBBY" && !room.session?.playerId,
    canEditCharacter: room.session?.principalType === "player" && room.status === "LOBBY",
    readyTotal,
    canStart: Boolean(room.session?.isHost)
      && room.status === "LOBBY"
      && playerTotal >= 3
      && readyTotal === playerTotal,
    canSubmitAction: room.session?.principalType === "player" && room.status === "COLLECTING_ACTIONS",
  };
}
