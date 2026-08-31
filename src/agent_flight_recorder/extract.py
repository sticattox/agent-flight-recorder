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
from .roles import AGENT_VISIBLE_ROLES, is_agent_visible

PHASE_RULES = [
    (
        "freeze",
        (
            "paused exactly",
            "no edits",
            "read-only",
            "not going to change",
            "won't modify",
            "will not edit",
            "no commits",
            "remain read-only",
            "stay frozen",
        ),
    ),
    (
        "inspect",
        (
            "inspect",
            "looking at",
            "checking",
            "ran ",
            "status --",
            "list the",
            "exists=",
            "rev-parse",
            "read the file",
        ),
    ),
    (
        "hypothesize",
        (
            "i'll distinguish",
            "might be",
            "could be",
            "hypothesis",
            "not the same thing",
            "suspect",
            "i think the cause",
            "working theory",
        ),
    ),
    (
        "diagnose",
        (
            "confirmed",
            "the boundary",
            "root cause",
            "this means",
            "walks upward",
            "not an independent",
            "diagnosis",
        ),
    ),
    (
        "observe",
        (
            "exists=true",
            "exists=false",
            "count=",
            "returned",
            "shows ",
            "untracked",
            "output was",
        ),
    ),
    (
        "revise",
        (
            "instead",
            "changing the plan",
            "do not resume",
            "safest preservation",
            "new plan",
            "rather than",
            "revising the plan",
        ),
    ),
    (
        "verify",
        (
            "test passed",
            "tests pass",
            "verified",
            "checksum",
            "hash-compare",
            "sha-256",
        ),
    ),
    ("execute", ("implement", "editing", "applying", "creating", "write the file", "commit")),
]

REFUSAL_MARKERS = (
    "no edits",
    "no commits",
    "no cleanup",
    "no resets",
    "will not",
    "won't",
    "refused",
    "not going to",
    "leave untouched",
    "do not clean",
    "never commit",
    "never reset",
    "never edit",
    "i will not",
)

# Present-tense, session-local failure. Historical narration is excluded separately.
FAILURE_MARKERS = (
    "failed with",
    "error:",
    "unexpected",
    "wrong git",
    "boundary issue",
    "assumption may be wrong",
    "assumption is now uncertain",
    "tests failed",
    "command failed",
)

RECOVERY_MARKERS = (
    "instead",
    "retry",
    "new plan",
    "revising",
    "paused exactly",
    "will not",
    "inspect",
    "freeze",
    "rather than",
    "checking candidate",
)

GOAL_MARKERS = ("goal", "task", "implement", "add ", "fix ", "build ")

# Reusable semantic cues only. No fixture fingerprints.
CUES_BY_ID = {
    "AFR-P001": (
        "paused exactly",
        "assumed project boundary",
        "assumption may be wrong",
        "assumption is now uncertain",
        "foundational assumption",
        "no edits, commits",
        "no edits, no cleanup",
        "read-only until",
        "freeze writes",
        "reduce mutation",
    ),
    "AFR-P002": (
        "same tests",
        "same questions",
        "candidate roots",
        "symmetrically",
        "same discriminating",
        "not the same thing",
        "distinguish",
    ),
    "AFR-P003": (
        "resume gate",
        "read-only until",
        "remain read-only",
        "no edits, no cleanup",
        "stay frozen",
        "will not resume",
        "paused exactly",
    ),
    "AFR-P004": (
        "project policy",
        "trusted baseline",
        "hash-compare",
        "excluding runtime",
        "policy excludes",
        "user-owned paths",
    ),
    "AFR-P005": (
        "leave the accidental",
        "specimen",
        "preserve partial",
        "preservation artifact",
    ),
    "AFR-P006": (
        "will not clean",
        "will not reset",
        "unrelated",
        "umbrella",
        "not the task",
        "dirt the current task does not own",
    ),
}

_HISTORICAL = re.compile(
    r"\b(yesterday|last week|previously|earlier today|the other day|once|used to)\b",
    re.IGNORECASE,
)
_MENTION_ONLY = re.compile(
    r"\b(the word|the token|appears in|mentioned in|documentation says|docs say)\b",
    re.IGNORECASE,
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _excerpt(text: str, limit: int = 280) -> str:
    compact = re.sub(r"\s+", " ", text.strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."


def _contains_cue(text: str, cue: str) -> bool:
    hay = _norm(text)
    needle = _norm(cue)
    if not needle:
        return False
    if " " in needle or len(needle) >= 10:
        return needle in hay
    return re.search(rf"\b{re.escape(needle)}\b", hay) is not None


def _prov(turn: Turn, text: str | None = None) -> Provenance:
    return Provenance(
        excerpt=_excerpt(text or turn.text),
        speaker=turn.speaker,
        role=turn.role,
        locator=turn.locator,
    )


def classify_phase(text: str) -> str | None:
    if _MENTION_ONLY.search(text):
        return None
    for phase, needles in PHASE_RULES:
        if any(_contains_cue(text, needle) for needle in needles):
            return phase
    return None


def first_user_goal(turns: list[Turn], meta: dict[str, str]) -> str:
    if meta.get("goal"):
        return meta["goal"]
    for turn in turns:
        if turn.role == "human":
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
        if turn.role == "human":
            continue
        if turn.role == "unknown":
            continue
        phase = classify_phase(turn.text)
        if not phase:
            continue
        if phase in {"hypothesize", "diagnose", "revise", "freeze", "execute"} and turn.role == "tool":
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
        if not is_agent_visible(turn.role):
            continue
        lowered = _norm(turn.text)
        if not any(w in lowered for w in ("confirmed", "because", "so i", "instead", "therefore", "new plan")):
            continue
        points.append(
            DecisionPoint(
                decision=_excerpt(turn.text, 180),
                evidence=_excerpt(turn.text, 220),
                provenance=[_prov(turn)],
            )
        )
    return points[:12]


def _is_current_failure(turn: Turn) -> bool:
    if turn.role == "human":
        return False
    if turn.role not in {"agent", "reasoning-visible", "tool"}:
        return False
    if _HISTORICAL.search(turn.text):
        return False
    if _MENTION_ONLY.search(turn.text):
        return False
    return any(_contains_cue(turn.text, marker) for marker in FAILURE_MARKERS)


def _recovery_from(turn: Turn | None) -> tuple[str, str | None, bool, str]:
    if turn is None:
        return "Not stated", None, False, "unresolved"
    if turn.role == "human":
        return "Not observed as an agent action", turn.role, False, "unresolved"
    if turn.role == "tool":
        return _excerpt(turn.text, 180), turn.role, False, "unresolved"
    if turn.role not in AGENT_VISIBLE_ROLES:
        return "Not stated", turn.role, False, "unresolved"
    observed = any(_contains_cue(turn.text, marker) for marker in RECOVERY_MARKERS)
    action = _excerpt(turn.text, 180)
    if observed:
        return action, turn.role, True, "observed"
    return action, turn.role, False, "unresolved"


def collect_failures(turns: list[Turn]) -> list[FailureRecovery]:
    items: list[FailureRecovery] = []
    for index, turn in enumerate(turns):
        if not _is_current_failure(turn):
            continue
        nxt = turns[index + 1] if index + 1 < len(turns) else None
        action, action_role, observed, status = _recovery_from(nxt)
        provenance = [_prov(turn)]
        if nxt and observed:
            provenance.append(_prov(nxt))
        items.append(
            FailureRecovery(
                failure=_excerpt(turn.text, 180),
                next_action=action,
                recovered=True if observed else None,
                failure_source_role=turn.role,
                recovery_action=action if observed else None,
                recovery_action_role=action_role if observed else None,
                recovery_observed=observed,
                recovery_status=status,
                provenance=provenance,
            )
        )
    return items[:10]


def collect_refusals(turns: list[Turn]) -> list[Claim]:
    claims: list[Claim] = []
    seen: set[str] = set()
    for turn in turns:
        if not is_agent_visible(turn.role):
            continue
        if _MENTION_ONLY.search(turn.text):
            continue
        if not any(_contains_cue(turn.text, marker) for marker in REFUSAL_MARKERS):
            continue
        statement = _excerpt(turn.text, 200)
        if statement in seen:
            continue
        seen.add(statement)
        claims.append(Claim(statement=statement, provenance=[_prov(turn)]))
    return claims


def _agent_blob(turns: list[Turn]) -> str:
    return "\n".join(t.text for t in turns if is_agent_visible(t.role))


def match_seed_patterns(turns: list[Turn]) -> list[ExtractedPattern]:
    visible = [t for t in turns if is_agent_visible(t.role)]
    if not visible:
        return []
    blob = _norm(_agent_blob(turns))
    found: list[ExtractedPattern] = []
    for seed in SEED_PATTERNS:
        extra = list(getattr(seed, "match_cues", []) or [])
        extra += list(CUES_BY_ID.get(seed.pattern_id, ()))
        cues = [_norm(c) for c in extra if c and len(_norm(c)) >= 8]
        hits = [cue for cue in cues if cue in blob]
        if len(hits) < 2:
            continue
        excerpt_turn = next((t for t in visible if any(_contains_cue(t.text, cue) for cue in hits)), visible[0])
        found.append(
            ExtractedPattern(
                pattern_id=seed.pattern_id,
                title=seed.title,
                trigger=seed.trigger_conditions[0] if seed.trigger_conditions else None,
                provenance=[_prov(excerpt_turn)],
            )
        )
    return found


def _coverage(trace: FlightTrace) -> float:
    groups = (
        trace.observable_process,
        trace.decision_points,
        trace.failures_recoveries,
        trace.anti_patterns_avoided,
        trace.patterns_extracted,
    )
    total = sum(len(group) for group in groups)
    if total == 0:
        return 0.0
    cited = sum(1 for group in groups for item in group if item.provenance)
    return cited / total


def confidence_for(trace: FlightTrace) -> dict[str, object]:
    coverage = _coverage(trace)
    cited = sum(
        1
        for group in (
            trace.observable_process,
            trace.decision_points,
            trace.anti_patterns_avoided,
            trace.failures_recoveries,
            trace.patterns_extracted,
        )
        for item in group
        if item.provenance
    )
    goal_known = bool(trace.goal) and trace.goal != "Unstated in transcript"
    agent_backed = any(
        any(p.role in AGENT_VISIBLE_ROLES for p in event.provenance)
        for event in trace.observable_process
    )
    if cited == 0 or coverage < 0.4:
        extraction = "low"
    elif goal_known and coverage >= 0.8 and agent_backed and cited >= 3:
        extraction = "high"
    elif goal_known and coverage >= 0.5 and agent_backed:
        extraction = "medium"
    else:
        extraction = "low"
    return {
        "extraction_confidence": extraction,
        "corroboration": 1,
        "provenance_coverage": round(coverage, 3),
        "strength": extraction,
        "cited_claims": cited,
        "notes": (
            "extraction_confidence is support inside this transcript. "
            "corroboration is independent sessions and stays 1 at ingest. "
            "Volume of cited fields does not by itself raise confidence."
        ),
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
