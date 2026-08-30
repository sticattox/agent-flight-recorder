from __future__ import annotations

import json
from pathlib import Path

from .extract import build_trace
from .library import empty_library, load_library, merge_trace, save_library
from .models import FlightTrace, PatternLibrary
from .parse import load_raw, maybe_json, parse_turns


def ingest_transcript(path: str | Path) -> FlightTrace:
    raw = load_raw(path)
    as_json = maybe_json(raw)
    if as_json and ("observable_process" in as_json or "schema_version" in as_json):
        return FlightTrace.from_dict(as_json)
    turns = parse_turns(raw)
    return build_trace(turns, raw, source_path=str(path))


def write_trace(trace: FlightTrace, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(trace.to_dict(), indent=2) + "\n", encoding="utf-8")


def merge_into_library(
    traces: list[FlightTrace],
    library_path: str | Path | None = None,
    include_seed: bool = True,
) -> PatternLibrary:
    library = load_library(library_path) if library_path and Path(library_path).exists() else empty_library(include_seed)
    for index, trace in enumerate(traces, start=1):
        merge_trace(library, trace, session_id=f"session-{index}")
    return library


def persist_library(library: PatternLibrary, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    save_library(library, path)
