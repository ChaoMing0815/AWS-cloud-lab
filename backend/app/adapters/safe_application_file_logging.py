from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


_SAFE_EVENT_KEYS = {
    "co_story.request": {
        "request_id",
        "method",
        "path",
        "status",
        "latency_ms",
    },
    "co_story.storyteller": {"operation", "failure_code"},
    "co_story.storyteller_schema": {
        "operation",
        "failure_code",
        "diagnostic_code",
    },
    "co_story.storyteller_metrics": {
        "metric_type",
        "operation",
        "latency_ms",
        "input_tokens",
        "output_tokens",
    },
    "co_story.storyteller_recovery": {
        "metric_type",
        "operation",
        "retry_count",
        "fallback_count",
    },
}
_active_handler: RotatingFileHandler | None = None
_previous_levels: dict[str, int] = {}


class _SafeJsonEventFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        expected_keys = _SAFE_EVENT_KEYS.get(record.name)
        if expected_keys is None:
            return False
        try:
            event = json.loads(record.getMessage())
        except (TypeError, ValueError):
            return False
        if not isinstance(event, dict) or set(event) != expected_keys:
            return False
        record.msg = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        record.args = ()
        return True


class _ProtectedRotatingFileHandler(RotatingFileHandler):
    def _protect_file(self) -> None:
        os.chmod(self.baseFilename, 0o640)

    def __init__(self, filename: str) -> None:
        super().__init__(
            filename,
            maxBytes=1024 * 1024,
            backupCount=2,
            encoding="utf-8",
        )
        self._protect_file()

    def doRollover(self) -> None:  # noqa: N802 - logging Handler API
        super().doRollover()
        self._protect_file()


def _remove_active_handler() -> None:
    global _active_handler
    if _active_handler is None:
        return
    for logger_name in _SAFE_EVENT_KEYS:
        logger = logging.getLogger(logger_name)
        logger.removeHandler(_active_handler)
        logger.setLevel(_previous_levels.pop(logger_name, logging.NOTSET))
    _active_handler.close()
    _active_handler = None


def configure_safe_application_file_logging(path: str | None) -> None:
    global _active_handler
    _remove_active_handler()
    if not path:
        return

    target = Path(path)
    if target.is_symlink():
        raise RuntimeError("CO_STORY_APPLICATION_LOG_PATH")
    handler = _ProtectedRotatingFileHandler(str(target))
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.addFilter(_SafeJsonEventFilter())

    for logger_name in _SAFE_EVENT_KEYS:
        logger = logging.getLogger(logger_name)
        _previous_levels[logger_name] = logger.level
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
    _active_handler = handler
