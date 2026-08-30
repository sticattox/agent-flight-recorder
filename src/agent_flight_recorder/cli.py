from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .library import empty_library, load_library, save_library
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
from .pipeline import ingest_transcript, merge_into_library, persist_library, write_trace
from .render import render_library, render_trace


def _prov_list(items: list) -> list[Provenance]:
    return [Provenance(**p) for p in items]


def _trace_from_json(path: str) -> FlightTrace:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return FlightTrace(
        schema_version=data.get("schema_version", "0.2.0"),
        session=SessionMeta(**data.get("session", {})),
        goal=data.get("goal", ""),
        observable_process=[
            ProcessEvent(
                phase=e["phase"],
                summary=e["summary"],
                provenance=_prov_list(e.get("provenance", [])),
            )
            for e in data.get("observable_process", [])
        ],
        decision_points=[
            DecisionPoint(
                decision=d["decision"],
                evidence=d.get("evidence", ""),
                plan_before=d.get("plan_before"),
                plan_after=d.get("plan_after"),
                provenance=_prov_list(d.get("provenance", [])),
            )
            for d in data.get("decision_points", [])
        ],
        failures_recoveries=[
            FailureRecovery(
                failure=f["failure"],
                next_action=f["next_action"],
                recovered=f.get("recovered"),
                provenance=_prov_list(f.get("provenance", [])),
            )
            for f in data.get("failures_recoveries", [])
        ],
        anti_patterns_avoided=[
            Claim(statement=c["statement"], provenance=_prov_list(c.get("provenance", [])))
            for c in data.get("anti_patterns_avoided", [])
        ],
        patterns_extracted=[
            ExtractedPattern(
                pattern_id=p.get("pattern_id"),
                title=p["title"],
                trigger=p.get("trigger"),
                evidence_count=p.get("evidence_count", 1),
                provenance=_prov_list(p.get("provenance", [])),
            )
            for p in data.get("patterns_extracted", [])
        ],
        confidence=data.get("confidence", {}),
        provenance_notes=data.get("provenance_notes"),
    )


def _cmd_ingest(args: argparse.Namespace) -> int:
    trace = ingest_transcript(args.transcript)
    if args.output:
        write_trace(trace, args.output)
    if args.print or not args.output:
        sys.stdout.write(render_trace(trace))
    if args.json_stdout:
        sys.stdout.write(json.dumps(trace.to_dict(), indent=2) + "\n")
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    sys.stdout.write(render_trace(_trace_from_json(args.trace)))
    return 0


def _cmd_library(args: argparse.Namespace) -> int:
    traces = [ingest_transcript(path) for path in args.transcripts]
    library = merge_into_library(traces, library_path=args.library, include_seed=not args.no_seed)
    persist_library(library, args.output)
    if args.print:
        sys.stdout.write(render_library(library))
    return 0


def _cmd_patterns(args: argparse.Namespace) -> int:
    if args.init:
        save_library(empty_library(include_seed=True), args.init)
        sys.stdout.write(f"Wrote seed library to {args.init}\n")
        return 0
    library = load_library(args.library)
    sys.stdout.write(render_library(library))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="afr",
        description="Turn observable AI development sessions into structured agent flight records.",
    )
    parser.add_argument("--version", action="version", version=f"agent-flight-recorder {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Transcript -> structured trace")
    ingest.add_argument("transcript")
    ingest.add_argument("-o", "--output", help="Write trace JSON to this path")
    ingest.add_argument("--print", action="store_true", help="Print the human-readable record")
    ingest.add_argument("--json-stdout", action="store_true", help="Also print JSON")
    ingest.set_defaults(func=_cmd_ingest)

    render = sub.add_parser("render", help="Pretty-print an existing trace JSON")
    render.add_argument("trace")
    render.set_defaults(func=_cmd_render)

    library = sub.add_parser("library", help="Merge sessions into a pattern library")
    library.add_argument("transcripts", nargs="+")
    library.add_argument("-o", "--output", required=True, help="Library JSON output")
    library.add_argument("--library", help="Existing library to update")
    library.add_argument("--no-seed", action="store_true", help="Do not start from seed patterns")
    library.add_argument("--print", action="store_true")
    library.set_defaults(func=_cmd_library)

    patterns = sub.add_parser("patterns", help="Show or initialize the pattern library")
    patterns.add_argument("--library", help="Library JSON to display")
    patterns.add_argument("--init", help="Write a seed library to this path")
    patterns.set_defaults(func=_cmd_patterns)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "patterns" and not args.library and not args.init:
        parser.error("patterns requires --library or --init")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
