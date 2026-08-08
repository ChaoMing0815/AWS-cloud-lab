from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from copy import deepcopy
from threading import RLock
from typing import Any

from app.application.ports import IdempotencyStore
from app.domain.errors import DomainError


class MemoryIdempotencyStore(IdempotencyStore):
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], tuple[str, Any]] = {}
        self._lock = RLock()

    def execute(
        self,
        scope: str,
        key: str,
        payload: dict[str, Any],
        operation: Callable[[], Any],
    ) -> Any:
        if not 8 <= len(key) <= 128 or any(character.isspace() for character in key):
            raise DomainError("INVALID_IDEMPOTENCY_KEY", "Idempotency-Key 格式無效。", 400)
        fingerprint = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        record_key = (scope, key)
        with self._lock:
            existing = self._records.get(record_key)
            if existing:
                previous_fingerprint, result = existing
                if previous_fingerprint != fingerprint:
                    raise DomainError(
                        "IDEMPOTENCY_KEY_REUSED",
                        "同一 Idempotency-Key 不可用於不同內容。",
                        422,
                    )
                return deepcopy(result)
            result = operation()
            self._records[record_key] = (fingerprint, deepcopy(result))
            return result
