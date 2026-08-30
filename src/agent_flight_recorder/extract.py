from __future__ import annotations

import re

from .catalog import SEED_PATTERNS
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
from .parse import Turn, extract_metadata

PHASE_RULES = [
    ("freeze", ("paused exactly", "no edits", "read-only", "not going to change", "freeze", "won't modify", "will not edit", "no commits", "no cleanup")),
    ("inspect", ("inspect", "looking at", "checking", "ran ", "status --", "list the", "exists=", "rev-parse", "read the file", "open ")),
    ("hypothesize", ("i'll distinguish", "might be", "could be", "hypothesis", "not the same thing", "suspect", "assumption")),
    ("diagnose", ("confirmed", "the boundary", "root cause", "this means", "walks upward", "not an independent", "diagnosis")),
    ("observe", ("output", "exists=true", "exists=false", "count=", "returned", "shows ", "untracked")),
    ("revise", ("instead", "changing the plan", "do not resume", "safest preservation", "new plan", "rather than")),
    ("verify", ("test passed", "tests pass", "verified", "checksum", "hash-compare", "sha-256", "restart")),
    ("execute", ("implement", "editing", "applying", "creating", "write the file", "commit")),
]

REFUSAL_MARKERS = (
    "no edits", "no commits", "no cleanup", "no resets", "will not", "won't",
    "refused", "not going to", "leave untouched", "do not clean", "never commit",
    "never reset", "never edit",
)
FAILURE_MARKERS = ("failed", "error", "unexpected", "wrong git", "boundary issue", "assumption", "uncommitted", "dirty")
GOAL_MARKERS = ("goal", "task", "implement", "add ", "fix ", "build ")

CUES_BY_ID = {
    "AFR-P001": ("paused exactly", "assumed project boundary", "assumption may be wrong", "assumption is now uncertain", "that assumption", "no edits, commits", "foundational assumption"),
    "AFR-P002": ("same tests", "same questions", "candidate roots", "symmetrically"),
    "AFR-P003": ("resume gate", "read-only until", "remain read-only", "no edits, no cleanup"),
    "AFR-P004": ("project policy", "trusted baseline", "hash-compare", "excluding"),
    "AFR-P005": ("leave the accidental", "specimen", "preserve", "partial work"),
    "AFR-P006": ("will not clean", "4,812", "unrelated", "umbrella"),
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _excerpt(text: str, limit: int = 280) -> str:
    compact = re.sub(r"\s+", " ", text.strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."


def _prov(turn: Turn, text: str | None = None) -> Provenance:
    return Provenance(excerpt=_excerpt(text or turn.text), speaker=turn.speaker, locator=turn.locator)


def classify_phase(text: str) -> str | None:
    lowered = _norm(text)
    for phase, needles in PHASE_RULES:
        if any(needle in lowered for needle in needles):
            return phase
    return None


def first_user_goal(turns: list[Turn], meta: dict[str, str]) -> str:
    if meta.get("goal"):
        return meta["goal"]
    for turn in turns:
        if turn.speaker in {"user", "human", "andrew"}:
            return _excerpt(turn.text, 400)
    for turn in turns:
        if any(marker in _norm(turn.text) for marker in GOAL_MARKERS):
            return _excerpt(turn.text, 400)
    return "Unstated in transcript"


def session_from_meta(meta: dict[str, str], source_path: str | None) -> SessionMeta:
    return SessionMeta(
        agent=meta.get("agent"),
        model=meta.get("model"),
        date=meta.get("date"),
        project=meta.get("project"),
        source_path=source_path,
    )


def collect_process(turns: list[Turn]) -> list[ProcessEvent]:
    events: list[ProcessEvent] = []
    seen: set[tuple[str, str]] = set()
    for turn in turns:
        if turn.speaker in {"user", "human"}:
            continue
        phase = classify_phase(turn.text)
        if not phase:
            continue
        summary = _excerpt(turn.text, 180)
        key = (phase, summary)
        if key in seen:
            continue
        seen.add(key)
        events.append(ProcessEvent(phase=phase, summary=summary, provenance=[_prov(turn)]))  # type: ignore[arg-type]
    return events


def collect_decisions(turns: list[Turn]) -> list[DecisionPoint]:
    points: list[DecisionPoint] = []
    for turn in turns:
        lowered = _norm(turn.text)
        if turn.speaker in {"user", "human"}:
            continue
        if not any(w in lowered for w in ("confirmed", "because", "so i", "instead", "therefore")):
            continue
        points.append(
            DecisionPoint(
                decision=_excerpt(turn.text, 180),
                evidence=_excerpt(turn.text, 220),
                provenance=[_prov(turn)],
            )
        )
    return points[:12]


def collect_failures(turns: list[Turn]) -> list[FailureRecovery]:
    items: list[FailureRecovery] = []
    for turn, nxt in zip(turns, turns[1:] + [None], strict=False):
        if not any(marker in _norm(turn.text) for marker in FAILURE_MARKERS):
            continue
        next_action = _excerpt(nxt.text, 180) if nxt else "Not stated"
        items.append(
            FailureRecovery(
                failure=_excerpt(turn.text, 180),
                next_action=next_action,
                provenance=[_prov(turn)],
            )
        )
    return items[:10]


def collect_refusals(turns: list[Turn]) -> list[Claim]:
    claims: list[Claim] = []
    seen: set[str] = set()
    for turn in turns:
        if not any(marker in _norm(turn.text) for marker in REFUSAL_MARKERS):
            continue
        statement = _excerpt(turn.text, 200)
        if statement in seen:
            continue
        seen.add(statement)
        claims.append(Claim(statement=statement, provenance=[_prov(turn)]))
    return claims


def match_seed_patterns(turns: list[Turn]) -> list[ExtractedPattern]:
    blob = _norm("\n".join(t.text for t in turns))
    found: list[ExtractedPattern] = []
    for seed in SEED_PATTERNS:
        extra = list(getattr(seed, "match_cues", []) or [])
        extra += list(CUES_BY_ID.get(seed.pattern_id, ()))
        extra += list(seed.trigger_conditions)
        cues = [_norm(c) for c in extra if c]
        keywords = [
            w
            for w in re.findall(r"[a-z0-9-]{5,}", _norm(seed.statement + " " + seed.title))
            if w not in {"before", "after", "against", "using", "those", "their", "other", "project", "rather"}
        ]
        cue_hit = any(cue in blob for cue in cues if len(cue) >= 12)
        hits = sum(1 for word in keywords if word in blob)
        if hits >= 3 or cue_hit:
            excerpt_turn = next(
                (
                    t
                    for t in turns
                    if any(cue in _norm(t.text) for cue in cues if len(cue) >= 12)
                    or any(w in _norm(t.text) for w in keywords[:8])
                ),
                turns[0],
            )
            found.append(
                ExtractedPattern(
                    pattern_id=seed.pattern_id,
                    title=seed.title,
                    trigger=seed.trigger_conditions[0] if seed.trigger_conditions else None,
                    provenance=[_prov(excerpt_turn)],
                )
            )
    return found


def confidence_for(trace: FlightTrace) -> dict[str, object]:
    cited = 0
    cited += sum(1 for e in trace.observable_process if e.provenance)
    cited += sum(1 for d in trace.decision_points if d.provenance)
    cited += sum(1 for c in trace.anti_patterns_avoided if c.provenance)
    total = (
        len(trace.observable_process)
        + len(trace.decision_points)
        + len(trace.anti_patterns_avoided)
        + len(trace.patterns_extracted)
    )
    if total == 0:
        strength = "low"
    elif cited >= 4 and trace.goal != "Unstated in transcript":
        strength = "medium"
    elif cited >= 8:
        strength = "high"
    else:
        strength = "low"
    return {
        "strength": strength,
        "cited_claims": cited,
        "total_structured_fields": total,
        "notes": "Heuristic extraction from visible transcript text only. Hidden chain-of-thought is out of scope.",
    }


def build_trace(turns: list[Turn], raw_text: str, source_path: str | None = None) -> FlightTrace:
    meta = extract_metadata(raw_text)
    trace = FlightTrace(
        session=session_from_meta(meta, source_path),
        goal=first_user_goal(turns, meta),
        observable_process=collect_process(turns),
        decision_points=collect_decisions(turns),
        failures_recoveries=collect_failures(turns),
        anti_patterns_avoided=collect_refusals(turns),
        patterns_extracted=match_seed_patterns(turns),
        provenance_notes="Every claim should carry a verbatim excerpt. Uncited statements are incomplete records.",
    )
    trace.confidence = confidence_for(trace)
    return trace
