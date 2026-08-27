class MockSupportModel:
    """Deterministic proposal adapter; application validation remains authoritative."""

    def __init__(self, *, proposal: object | None = None) -> None:
        self._proposal = proposal
        self._received_messages: list[str] = []

    def propose(self, message: str) -> object:
        self._received_messages.append(message)
        if self._proposal is not None:
            return self._proposal
        lowered = message.casefold()
        report_markers = ("問題回報", "錯誤", "無法", "沒有反應", "bug")
        if any(marker in lowered for marker in report_markers):
            return {"tool": "draft_problem_report", "arguments": {"description": message}}
        return {"tool": "lookup_game_rules", "arguments": {"query": message}}

    @property
    def received_messages(self) -> tuple[str, ...]:
        return tuple(self._received_messages)
