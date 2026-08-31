from __future__ import annotations

import copy
import json
from pathlib import Path

from .catalog import SEED_PATTERNS, seed_by_id
from .models import FlightTrace, PatternLibrary, PatternRecord


def empty_library(include_seed: bool = True) -> PatternLibrary:
    patterns = [copy.deepcopy(p) for p in SEED_PATTERNS] if include_seed else []
    return PatternLibrary(patterns=patterns)


def load_library(path: str | Path) -> PatternLibrary:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    allowed = PatternRecord.__dataclass_fields__.keys()
    patterns = []
    for item in data.get("patterns", []):
        filtered = {k: v for k, v in item.items() if k in allowed}
        patterns.append(PatternRecord(**filtered))
    return PatternLibrary(schema_version=data.get("schema_version", "0.2.0"), patterns=patterns)


def save_library(library: PatternLibrary, path: str | Path) -> None:
    Path(path).write_text(json.dumps(library.to_dict(), indent=2) + "\n", encoding="utf-8")


def session_label(trace: FlightTrace, fallback: str) -> str:
    parts = [trace.session.date, trace.session.agent or trace.session.model, trace.session.project]
    label = " / ".join(p for p in parts if p)
    return label or fallback


def merge_trace(library: PatternLibrary, trace: FlightTrace, session_id: str | None = None) -> PatternLibrary:
    """Attach a trace's extracted patterns onto the library.

    Matching is by stable pattern_id when present.
    """
    known = library.by_id()
    seeds = seed_by_id()
    label = session_label(trace, session_id or trace.session.source_path or "session")
    model = trace.session.model or trace.session.agent

    for extracted in trace.patterns_extracted:
        pid = extracted.pattern_id
        if pid and pid in known:
            record = known[pid]
        elif pid and pid in seeds:
            record = copy.deepcopy(seeds[pid])
            library.patterns.append(record)
            known[pid] = record
        elif pid:
            record = PatternRecord(pattern_id=pid, title=extracted.title, statement=extracted.title)
            library.patterns.append(record)
            known[pid] = record
        else:
            continue

        if label not in record.evidence_sessions:
            record.evidence_sessions.append(label)
        if model and model not in record.models_observed:
            record.models_observed.append(model)
        for excerpt in extracted.provenance:
            payload = excerpt.to_dict()
            payload["session"] = label
            if payload not in record.source_excerpts:
                record.source_excerpts.append(payload)
        if extracted.trigger and extracted.trigger not in record.trigger_conditions:
            record.trigger_conditions.append(extracted.trigger)
        n = len(record.evidence_sessions)
        extraction = (trace.confidence or {}).get("extraction_confidence")
        if n >= 5 and extraction == "high":
            record.confidence = "high"
        elif n >= 2 and extraction in {"medium", "high"}:
            record.confidence = "medium"
        else:
            record.confidence = "low" if extraction == "low" else (record.confidence or "low")
    return library
