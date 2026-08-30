from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


Phase = Literal[
    "inspect",
    "hypothesize",
    "execute",
    "observe",
    "diagnose",
    "revise",
    "verify",
    "freeze",
    "escalate",
]


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


@dataclass
class Provenance:
    excerpt: str
    speaker: str = "agent"
    locator: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if data["locator"] is None:
            data.pop("locator")
        return data


@dataclass
class ProcessEvent:
    phase: Phase
    summary: str
    provenance: list[Provenance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "summary": self.summary,
            "provenance": [p.to_dict() for p in self.provenance],
        }


@dataclass
class DecisionPoint:
    decision: str
    evidence: str
    plan_before: str | None = None
    plan_after: str | None = None
    provenance: list[Provenance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "decision": self.decision,
            "evidence": self.evidence,
            "plan_before": self.plan_before,
            "plan_after": self.plan_after,
            "provenance": [p.to_dict() for p in self.provenance],
        }
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class FailureRecovery:
    failure: str
    next_action: str
    recovered: bool | None = None
    provenance: list[Provenance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "failure": self.failure,
            "next_action": self.next_action,
            "recovered": self.recovered,
            "provenance": [p.to_dict() for p in self.provenance],
        }
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class Claim:
    statement: str
    provenance: list[Provenance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "statement": self.statement,
            "provenance": [p.to_dict() for p in self.provenance],
        }


@dataclass
class ExtractedPattern:
    pattern_id: str | None
    title: str
    trigger: str | None = None
    evidence_count: int = 1
    provenance: list[Provenance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["provenance"] = [p.to_dict() for p in self.provenance]
        if data["pattern_id"] is None:
            data.pop("pattern_id")
        if data["trigger"] is None:
            data.pop("trigger")
        return data


@dataclass
class SessionMeta:
    agent: str | None = None
    model: str | None = None
    date: str | None = None
    project: str | None = None
    source_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class FlightTrace:
    schema_version: str = "0.2.0"
    session: SessionMeta = field(default_factory=SessionMeta)
    goal: str = ""
    observable_process: list[ProcessEvent] = field(default_factory=list)
    decision_points: list[DecisionPoint] = field(default_factory=list)
    failures_recoveries: list[FailureRecovery] = field(default_factory=list)
    anti_patterns_avoided: list[Claim] = field(default_factory=list)
    patterns_extracted: list[ExtractedPattern] = field(default_factory=list)
    confidence: dict[str, Any] = field(default_factory=dict)
    provenance_notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "schema_version": self.schema_version,
            "session": self.session.to_dict(),
            "goal": self.goal,
            "observable_process": [e.to_dict() for e in self.observable_process],
            "decision_points": [d.to_dict() for d in self.decision_points],
            "failures_recoveries": [f.to_dict() for f in self.failures_recoveries],
            "anti_patterns_avoided": [c.to_dict() for c in self.anti_patterns_avoided],
            "patterns_extracted": [p.to_dict() for p in self.patterns_extracted],
            "confidence": self.confidence,
        }
        if self.provenance_notes:
            data["provenance_notes"] = self.provenance_notes
        return _clean(data)


@dataclass
class PatternRecord:
    pattern_id: str
    title: str
    statement: str
    trigger_conditions: list[str] = field(default_factory=list)
    recovery_sequences: list[str] = field(default_factory=list)
    evidence_sessions: list[str] = field(default_factory=list)
    counterexamples: list[str] = field(default_factory=list)
    models_observed: list[str] = field(default_factory=list)
    confidence: str = "low"
    source_excerpts: list[dict[str, Any]] = field(default_factory=list)
    match_cues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("match_cues", None)
        return data


@dataclass
class PatternLibrary:
    schema_version: str = "0.2.0"
    patterns: list[PatternRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "patterns": [p.to_dict() for p in self.patterns],
        }

    def by_id(self) -> dict[str, PatternRecord]:
        return {p.pattern_id: p for p in self.patterns}
