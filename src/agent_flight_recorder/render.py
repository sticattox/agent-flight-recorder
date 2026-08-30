from __future__ import annotations

from .models import FlightTrace, PatternLibrary


def render_trace(trace: FlightTrace) -> str:
    session = trace.session.to_dict()
    lines = [
        "SESSION",
        f"  agent / model / date / project: "
        f"{session.get('agent') or '-'} / {session.get('model') or '-'} / "
        f"{session.get('date') or '-'} / {session.get('project') or '-'}",
        "",
        "GOAL",
        f"  {trace.goal or '-'}",
        "",
        "OBSERVABLE PROCESS",
    ]
    if not trace.observable_process:
        lines.append("  (none extracted)")
    for event in trace.observable_process:
        lines.append(f"  {event.phase}: {event.summary}")
    lines += ["", "DECISION POINTS"]
    if not trace.decision_points:
        lines.append("  (none extracted)")
    for item in trace.decision_points:
        lines.append(f"  - {item.decision}")
        lines.append(f"    evidence: {item.evidence}")
    lines += ["", "FAILURES / RECOVERIES"]
    if not trace.failures_recoveries:
        lines.append("  (none extracted)")
    for item in trace.failures_recoveries:
        lines.append(f"  failure: {item.failure}")
        lines.append(f"  next:    {item.next_action}")
    lines += ["", "ANTI-PATTERNS AVOIDED"]
    if not trace.anti_patterns_avoided:
        lines.append("  (none extracted)")
    for claim in trace.anti_patterns_avoided:
        lines.append(f"  - {claim.statement}")
    lines += ["", "PATTERNS EXTRACTED"]
    if not trace.patterns_extracted:
        lines.append("  (none extracted)")
    for pattern in trace.patterns_extracted:
        pid = pattern.pattern_id or "unassigned"
        lines.append(f"  {pid} - {pattern.title}")
    strength = trace.confidence.get("strength", "unknown")
    lines += [
        "",
        "CONFIDENCE",
        f"  {strength} ({trace.confidence.get('cited_claims', 0)} cited claims)",
        "",
        "PROVENANCE",
    ]
    excerpts = []
    for group in (
        trace.observable_process,
        trace.decision_points,
        trace.failures_recoveries,
        trace.anti_patterns_avoided,
        trace.patterns_extracted,
    ):
        for item in group:
            excerpts.extend(item.provenance)
    if not excerpts:
        lines.append("  (no excerpts)")
    for prov in excerpts[:20]:
        loc = f" [{prov.locator}]" if prov.locator else ""
        lines.append(f"  - {prov.speaker}{loc}: {prov.excerpt}")
    return "\n".join(lines) + "\n"


def render_library(library: PatternLibrary) -> str:
    lines = ["PATTERN LIBRARY", ""]
    for pattern in library.patterns:
        lines += [
            f"{pattern.pattern_id} - {pattern.title}",
            f"  statement: {pattern.statement}",
            f"  confidence: {pattern.confidence}",
            f"  evidence sessions: {len(pattern.evidence_sessions)}",
            f"  models: {', '.join(pattern.models_observed) or '-'}",
            f"  triggers: {'; '.join(pattern.trigger_conditions) or '-'}",
            "",
        ]
    return "\n".join(lines)
