from __future__ import annotations

import base64
import hmac
import secrets

from app.application.ports import SessionTokenFactory


class HmacSessionTokenFactory(SessionTokenFactory):
    def __init__(self, secret: bytes | None = None) -> None:
        self._secret = secret or secrets.token_bytes(32)

    def derive(self, purpose: str, idempotency_key: str) -> str:
        digest = hmac.new(
            self._secret,
            f"{purpose}:{idempotency_key}".encode(),
            "sha256",
        ).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")
