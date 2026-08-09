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
        : room.status === "AWAITING_HOST"
          ? "所有玩家已提交，等待房主擲骰。"
          : room.status === "AWAITING_SPARK"
            ? "骰點已揭曉，等待玩家決定是否使用星火。"
            : room.status === "RESOLVING"
              ? "星火決策已完成，等待房主結算回合。"
              : room.status === "COMPLETION_AVAILABLE"
                ? "共同目標已完成，等待房主選擇結束或繼續探索。"
                : room.status === "COMPLETED"
                  ? "故事已完成，可查看最終結局。"
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
    canSubmitAction: room.session?.principalType === "player"
      && ["COLLECTING_ACTIONS", "AWAITING_HOST"].includes(room.status),
    canRoll: Boolean(room.session?.isHost) && room.status === "AWAITING_HOST",
    canResolve: Boolean(room.session?.isHost)
      && ["AWAITING_SPARK", "RESOLVING"].includes(room.status),
    currentDiceResult: (room.diceResults ?? []).find(
      (result) => result.playerId === room.session?.playerId,
    ) ?? null,
    canDecideSpark: room.session?.principalType === "player"
      && room.status === "AWAITING_SPARK"
      && (room.diceResults ?? []).some(
        (result) => result.playerId === room.session?.playerId && result.sparkDecision === "PENDING",
      ),
    progressPoints: room.progressPoints ?? 0,
    dangerPoints: room.dangerPoints ?? 0,
    gameProgressPercent: room.progressPercent ?? 0,
    dangerPercent: room.dangerPercent ?? 0,
    canFinishNow: Boolean(room.session?.isHost) && room.status === "COMPLETION_AVAILABLE",
    canContinue: Boolean(room.session?.isHost) && room.status === "COMPLETION_AVAILABLE",
    isCompleted: room.status === "COMPLETED",
    endingResultLabel: {
      FULL_SUCCESS: "完整成功",
      PARTIAL_SUCCESS: "部分成功",
      FAILURE: "主要目標失敗",
    }[room.endingResult] ?? "",
    endingCostLabel: {
      LOW: "低代價",
      SIGNIFICANT: "明確代價",
      MAJOR: "重大代價",
    }[room.endingCost] ?? "",
    pendingProgress: room.pendingProgress ?? 0,
    pendingDanger: room.pendingDanger ?? 0,
    diceResults: (room.diceResults ?? []).map((result) => ({
      ...result,
      playerName: room.players.find((player) => player.id === result.playerId)?.name ?? "未知玩家",
    })),
  };
}
