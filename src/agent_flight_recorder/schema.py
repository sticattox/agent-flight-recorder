"""Minimal draft-2020 subset used in tests. No runtime JSON Schema dependency."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "trace.schema.json"

PHASES = {
    "inspect",
    "hypothesize",
    "execute",
    "observe",
    "diagnose",
    "revise",
    "verify",
    "freeze",
    "escalate",
}
ROLES = {"human", "agent", "tool", "system", "reasoning-visible", "unknown"}
RECOVERY_STATUS = {"observed", "unresolved", "none"}


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_trace_dict(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["trace is not an object"]
    for key in ("schema_version", "session", "goal"):
        if key not in data:
            errors.append(f"missing {key}")
    allowed = {
        "schema_version",
        "session",
        "goal",
        "observable_process",
        "decision_points",
        "failures_recoveries",
        "anti_patterns_avoided",
        "patterns_extracted",
        "confidence",
        "provenance_notes",
    }
    extra = set(data) - allowed
    if extra:
        errors.append(f"unexpected keys: {sorted(extra)}")
    if "session" in data and not isinstance(data["session"], dict):
        errors.append("session must be an object")
    for event in data.get("observable_process") or []:
        if event.get("phase") not in PHASES:
            errors.append(f"invalid phase: {event.get('phase')}")
        if "summary" not in event:
            errors.append("process event missing summary")
        for prov in event.get("provenance") or []:
            if not prov.get("excerpt"):
                errors.append("provenance missing excerpt")
            role = prov.get("role")
            if role is not None and role not in ROLES:
                errors.append(f"invalid provenance role: {role}")
    for item in data.get("failures_recoveries") or []:
        if "failure" not in item or "next_action" not in item:
            errors.append("failure_recovery missing required fields")
        status = item.get("recovery_status")
        if status is not None and status not in RECOVERY_STATUS:
            errors.append(f"invalid recovery_status: {status}")
    return errors
