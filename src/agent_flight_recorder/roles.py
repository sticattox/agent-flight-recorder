"""Canonical speaker-role normalization.

Transcript labels are messy. Extractors must never invent their own
alias lists. Map once here, then filter by semantic role.
"""

from __future__ import annotations

from typing import Literal

Role = Literal["human", "agent", "tool", "system", "reasoning-visible", "unknown"]

ROLES: tuple[str, ...] = (
    "human",
    "agent",
    "tool",
    "system",
    "reasoning-visible",
    "unknown",
)

# Visible agent work product. Status panes and thoughts are not hidden CoT
# when they appear as labeled transcript lines.
AGENT_VISIBLE_ROLES = frozenset({"agent", "reasoning-visible"})
NON_HUMAN_ROLES = frozenset({"agent", "reasoning-visible", "tool", "system"})

_ALIAS_TO_ROLE: dict[str, Role] = {
    "user": "human",
    "human": "human",
    "andrew": "human",
    "operator": "human",
    "you": "human",
    "assistant": "agent",
    "agent": "agent",
    "codex": "agent",
    "grok": "agent",
    "chatgpt": "agent",
    "claude": "agent",
    "model": "agent",
    "tool": "tool",
    "function": "tool",
    "system": "system",
    "status": "reasoning-visible",
    "thought": "reasoning-visible",
    "thinking": "reasoning-visible",
}


def normalize_role(speaker: str | None) -> Role:
    if not speaker:
        return "unknown"
    key = speaker.strip().lower()
    return _ALIAS_TO_ROLE.get(key, "unknown")


def is_human(speaker_or_role: str) -> bool:
    return normalize_role(speaker_or_role) == "human" or speaker_or_role == "human"


def is_agent_visible(speaker_or_role: str) -> bool:
    role = speaker_or_role if speaker_or_role in ROLES else normalize_role(speaker_or_role)
    return role in AGENT_VISIBLE_ROLES
