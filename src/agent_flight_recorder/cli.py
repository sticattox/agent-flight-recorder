from __future__ import annotations

import argparse
import sys

from . import __version__
from .library import empty_library, save_library
from .pipeline import ingest_transcript, merge_into_library, persist_library, write_trace
from .render import render_library, render_trace


def _cmd_ingest(args: argparse.Namespace) -> int:
    trace = ingest_transcript(args.transcript)
    if args.output:
        write_trace(trace, args.output)
    if args.print or not args.output:
        sys.stdout.write(render_trace(trace))
    if args.json_stdout:
        import json

        sys.stdout.write(json.dumps(trace.to_dict(), indent=2) + "\n")
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    sys.stdout.write(render_trace(ingest_transcript(args.trace)))
    return 0


def _cmd_library(args: argparse.Namespace) -> int:
    traces = [ingest_transcript(path) for path in args.transcripts]
    library = merge_into_library(traces, library_path=args.library, include_seed=not args.no_seed)
    persist_library(library, args.output)
    if args.print:
        sys.stdout.write(render_library(library))
    return 0


def _cmd_patterns(args: argparse.Namespace) -> int:
    from .library import load_library

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
