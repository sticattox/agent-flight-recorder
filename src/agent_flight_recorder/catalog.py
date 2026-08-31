"""Seed operating policies extracted from observable agent work.

These are general coding-agent policies. They are not product internals.
IDs are stable so later sessions can accumulate evidence.
"""

from __future__ import annotations

from .models import PatternRecord


SEED_PATTERNS: list[PatternRecord] = [
    PatternRecord(
        pattern_id="AFR-P001",
        title="Reduce mutation authority when foundational assumptions become uncertain",
        statement=(
            "When an environmental invariant looks false, freeze writes. "
            "Re-establish ground truth before continuing implementation."
        ),
        trigger_conditions=[
            "Tool UI or workspace state contradicts the assumed project boundary",
            "Partial work exists inside a possibly inherited parent environment",
            "The agent cannot name the governing root, process, or install target",
        ],
        recovery_sequences=[
            "Freeze mutation",
            "Inspect candidate explanations symmetrically",
            "Quantify task-owned versus environment-owned state",
            "Compare against a trusted baseline",
            "Preserve partial work",
            "Propose a bounded repair target",
            "Resume only after the resume gate passes",
        ],
        confidence="medium",
        match_cues=[
            "paused exactly",
            "assumption may be wrong",
            "foundational assumption",
            "reduce mutation",
        ],
    ),
    PatternRecord(
        pattern_id="AFR-P002",
        title="Probe candidate explanations symmetrically",
        statement=(
            "Generate candidate states first. Apply the same discriminating tests "
            "to each. Compare results. Then rank. Do not inspect the favored "
            "hypothesis one way and the alternatives by vibe."
        ),
        trigger_conditions=[
            "More than one plausible location, process, config, or install could be live",
            "A folder, service, or copy looks separate but may inherit a parent",
        ],
        recovery_sequences=[
            "List candidate states",
            "Define one test battery",
            "Run the same tests on every candidate",
            "Compare tabulated results",
        ],
        confidence="medium",
        match_cues=["same tests", "same questions", "candidate roots", "symmetrically"],
    ),
    PatternRecord(
        pattern_id="AFR-P003",
        title="Do not leave diagnostic mode until the resume gate passes",
        statement=(
            "Remain read-only or escalate until governing boundary, task-owned "
            "state, trusted baseline, preservation artifact, and bounded mutation "
            "target are all known."
        ),
        trigger_conditions=[
            "The agent is mid-implementation and an assumption broke",
            "Any resume-gate field is still unknown",
        ],
        recovery_sequences=[
            "Stay frozen",
            "Fill missing gate fields with measurements",
            "Escalate if a field cannot be known from this environment",
        ],
        confidence="medium",
        match_cues=["resume gate", "remain read-only", "stay frozen", "read-only until"],
    ),
    PatternRecord(
        pattern_id="AFR-P004",
        title="Compare against a trusted baseline using project policy excludes",
        statement=(
            "Hash or diff the task tree against the last trusted baseline. Exclude "
            "runtime or user-owned paths supplied by project policy, not by "
            "hard-coded folder names from some other project."
        ),
        trigger_conditions=[
            "Need to know what changed without importing caches, secrets, or user data",
        ],
        recovery_sequences=[
            "Load runtime_or_user_owned_paths from project policy",
            "Compare task_tree to trusted_baseline with those excludes",
        ],
        confidence="medium",
        match_cues=["trusted baseline", "hash-compare", "project policy", "policy excludes"],
    ),
    PatternRecord(
        pattern_id="AFR-P005",
        title="Preserve partial work before repairing the environment that contains it",
        statement=(
            "Do not clean, reset, or relocate an environment until the in-flight "
            "work is inventoried and a preservation specimen exists."
        ),
        trigger_conditions=[
            "Partial implementation sits inside a dirty or wrong environment",
            "A cleanup or repo-init looks like the fastest fix",
        ],
        recovery_sequences=[
            "Inventory task-owned files",
            "Keep the accidental tree untouched as a specimen",
            "Copy only source-eligible files into a bounded target",
            "Prove transfer integrity before new edits",
        ],
        confidence="medium",
        match_cues=["specimen", "preserve partial", "leave the accidental", "preservation artifact"],
    ),
    PatternRecord(
        pattern_id="AFR-P006",
        title="Leave unrelated environmental dirt outside the task authority",
        statement=(
            "A huge dirty parent tree is not the task diff. Do not clean what the "
            "current job does not own."
        ),
        trigger_conditions=[
            "UI reports an implausible number of untracked or dirty files",
            "Most dirt belongs to unrelated tools or projects",
        ],
        recovery_sequences=[
            "Bucket dirt by top-level owner",
            "Scope status to the task prefix",
            "Refuse repo-wide clean/reset",
        ],
        confidence="medium",
        match_cues=["will not clean", "will not reset", "umbrella", "not the task"],
    ),
]


def seed_by_id() -> dict[str, PatternRecord]:
    return {p.pattern_id: p for p in SEED_PATTERNS}
