from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any, Protocol


ALARM_STATES = {"OK", "ALARM"}
SERVICE_STATES = {"active", "inactive"}
RECOMMENDED_ACTIONS = {
    "NO_ACTION",
    "RUN_HEALTH_CHECK",
    "RESTART_APPLICATION",
    "CHECK_DATABASE",
}
_REQUEST_KEYS = {"request_id", "method", "path", "status", "latency_ms"}
_STORYTELLER_KEYS = {"operation", "failure_code"}
_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
_STORYTELLER_OPERATIONS = {"generate_world", "resolve_round", "resolve_ending"}
_STORYTELLER_FAILURES = {
    "AUTHORIZATION_ERROR",
    "CONTENT_REJECTED",
    "INVALID_MODEL",
    "SCHEMA_INVALID",
    "THROTTLED",
    "TIMEOUT",
    "TRANSIENT_SERVICE_ERROR",
}


class IncidentAnalysisFailure(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class IncidentAdvisor(Protocol):
    def advise(self, facts: dict[str, Any]) -> dict[str, Any]: ...


class IncidentAnalyzer:
    def __init__(self, advisor: IncidentAdvisor, *, max_lines: int = 200) -> None:
        if isinstance(max_lines, bool) or not 1 <= max_lines <= 200:
            raise ValueError("max_lines")
        self._advisor = advisor
        self._max_lines = max_lines

    def analyze(
        self,
        log_path: Path,
        *,
        alarm_state: str,
        service_state: str,
    ) -> dict[str, Any]:
        if alarm_state not in ALARM_STATES:
            raise ValueError("alarm_state")
        if service_state not in SERVICE_STATES:
            raise ValueError("service_state")

        path = Path(log_path)
        if path.is_symlink() or not path.is_file():
            raise ValueError("log_path")

        with path.open(encoding="utf-8") as handle:
            lines = deque(handle, maxlen=self._max_lines)

        requests: list[dict[str, Any]] = []
        storyteller_failures: list[dict[str, str]] = []
        discarded = 0
        for line in lines:
            event = _safe_event(line)
            if event is None:
                discarded += 1
            elif set(event) == _REQUEST_KEYS:
                requests.append(
                    {
                        "method": event["method"],
                        "path": event["path"],
                        "status": event["status"],
                        "latency_ms": event["latency_ms"],
                    }
                )
            else:
                storyteller_failures.append(event)

        latest_5xx = [event for event in requests if 500 <= event["status"] <= 599][-5:]
        facts = {
            "alarm_state": alarm_state,
            "service_state": service_state,
            "window": {
                "scanned_lines": len(lines),
                "accepted_events": len(requests) + len(storyteller_failures),
                "discarded_lines": discarded,
            },
            "request_summary": {
                "total": len(requests),
                "status_5xx": len([event for event in requests if 500 <= event["status"] <= 599]),
                "latest_5xx": latest_5xx,
            },
            "storyteller_failures": storyteller_failures[-5:],
        }
        return validate_incident_report(self._advisor.advise(facts))


def validate_incident_report(report: Any) -> dict[str, Any]:
    expected_keys = {
        "summary",
        "probable_cause",
        "evidence",
        "recommended_action",
        "requires_human_approval",
    }
    if not isinstance(report, dict) or set(report) != expected_keys:
        raise IncidentAnalysisFailure("SCHEMA_INVALID")
    summary = _bounded_text(report["summary"], 600)
    probable_cause = _bounded_text(report["probable_cause"], 600)
    evidence = report["evidence"]
    if not isinstance(evidence, list) or not 1 <= len(evidence) <= 5:
        raise IncidentAnalysisFailure("SCHEMA_INVALID")
    normalized_evidence = [_bounded_text(item, 300) for item in evidence]
    if report["recommended_action"] not in RECOMMENDED_ACTIONS:
        raise IncidentAnalysisFailure("SCHEMA_INVALID")
    if report["requires_human_approval"] is not True:
        raise IncidentAnalysisFailure("SCHEMA_INVALID")
    return {
        "summary": summary,
        "probable_cause": probable_cause,
        "evidence": normalized_evidence,
        "recommended_action": report["recommended_action"],
        "requires_human_approval": True,
    }


def _bounded_text(value: Any, maximum: int) -> str:
    if not isinstance(value, str):
        raise IncidentAnalysisFailure("SCHEMA_INVALID")
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        raise IncidentAnalysisFailure("SCHEMA_INVALID")
    return normalized


def _safe_event(line: str) -> dict[str, Any] | None:
    try:
        event = json.loads(line)
    except (TypeError, ValueError):
        return None
    if not isinstance(event, dict):
        return None
    if set(event) == _REQUEST_KEYS and _valid_request_event(event):
        return event
    if set(event) == _STORYTELLER_KEYS and _valid_storyteller_event(event):
        return event
    return None


def _valid_request_event(event: dict[str, Any]) -> bool:
    request_id = event["request_id"]
    method = event["method"]
    path = event["path"]
    status = event["status"]
    latency_ms = event["latency_ms"]
    return (
        isinstance(request_id, str)
        and 1 <= len(request_id) <= 128
        and isinstance(method, str)
        and method in _HTTP_METHODS
        and isinstance(path, str)
        and path.startswith("/")
        and "?" not in path
        and len(path) <= 512
        and isinstance(status, int)
        and not isinstance(status, bool)
        and 100 <= status <= 599
        and isinstance(latency_ms, int)
        and not isinstance(latency_ms, bool)
        and 0 <= latency_ms <= 300_000
    )


def _valid_storyteller_event(event: dict[str, Any]) -> bool:
    operation = event["operation"]
    failure_code = event["failure_code"]
    return (
        isinstance(operation, str)
        and operation in _STORYTELLER_OPERATIONS
        and isinstance(failure_code, str)
        and failure_code in _STORYTELLER_FAILURES
    )
