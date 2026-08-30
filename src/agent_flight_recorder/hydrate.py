from __future__ import annotations

from typing import Any

from .models import (
    Claim,
    DecisionPoint,
    ExtractedPattern,
    FailureRecovery,
    FlightTrace,
    ProcessEvent,
    Provenance,
    SessionMeta,
)


def _fields(klass, payload: dict[str, Any]) -> dict[str, Any]:
    allowed = klass.__dataclass_fields__.keys()
    return {k: v for k, v in payload.items() if k in allowed}


def _prov(items: list) -> list[Provenance]:
    return [Provenance(**_fields(Provenance, p)) for p in items]


def trace_from_dict(data: dict[str, Any]) -> FlightTrace:
    session_raw = data.get("session") or {}
    return FlightTrace(
        schema_version=data.get("schema_version", "0.2.0"),
        session=SessionMeta(**_fields(SessionMeta, session_raw)),
        goal=data.get("goal", ""),
        observable_process=[
            ProcessEvent(
                phase=e["phase"],
                summary=e.get("summary", ""),
                provenance=_prov(e.get("provenance", [])),
            )
            for e in data.get("observable_process", [])
        ],
        decision_points=[
            DecisionPoint(
                **_fields(DecisionPoint, {**d, "provenance": _prov(d.get("provenance", []))})
            )
            for d in data.get("decision_points", [])
        ],
        failures_recoveries=[
            FailureRecovery(
                **_fields(FailureRecovery, {**f, "provenance": _prov(f.get("provenance", []))})
            )
            for f in data.get("failures_recoveries", [])
        ],
        anti_patterns_avoided=[
            Claim(statement=c["statement"], provenance=_prov(c.get("provenance", [])))
            for c in data.get("anti_patterns_avoided", [])
        ],
        patterns_extracted=[
            ExtractedPattern(
                **_fields(ExtractedPattern, {**p, "provenance": _prov(p.get("provenance", []))})
            )
            for p in data.get("patterns_extracted", [])
        ],
        confidence=data.get("confidence") or {},
        provenance_notes=data.get("provenance_notes"),
    )
