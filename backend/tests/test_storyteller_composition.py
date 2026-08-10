import inspect

from app.main import create_app


class StubStoryteller:
    def resolve_round(self, _room) -> str:
        return "測試敘事"

    def resolve_ending(self, _room) -> str:
        return "測試結局"


def test_create_app_accepts_and_uses_storyteller_dependency() -> None:
    signature = inspect.signature(create_app)

    assert "storyteller" in signature.parameters

    storyteller = StubStoryteller()
    app = create_app(storyteller=storyteller)

    assert app.state.room_service.storyteller is storyteller
