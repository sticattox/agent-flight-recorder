from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


SPEAKER_RE = re.compile(
    r"^(?P<speaker>User|Human|Andrew|Assistant|Agent|Codex|Grok|ChatGPT|System|Tool|Thought|Thinking|Status)"
    r"\s*[:\-]\s*(?P<body>.*)$",
    re.IGNORECASE,
)

META_RE = re.compile(
    r"^(agent|model|date|project|goal|source)\s*[:\-]\s*(.+)$",
    re.IGNORECASE,
)


@dataclass
class Turn:
    speaker: str
    text: str
    index: int

    @property
    def locator(self) -> str:
        return f"turn:{self.index}:{self.speaker}"


def load_raw(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def maybe_json(text: str) -> dict | None:
    stripped = text.strip()
    if not stripped.startswith("{"):
        return None
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def parse_turns(text: str) -> list[Turn]:
    """Split a transcript into speaker turns.

    Accepts markdown-ish logs:
      User: ...
      Agent: ...
      Thinking: ...
    Unlabeled continuation lines stay with the current speaker.
    If no speakers are found, the whole document is one agent turn.
    """
    turns: list[Turn] = []
    current_speaker = "agent"
    current_lines: list[str] = []
    index = 0

    def flush() -> None:
        nonlocal index, current_lines
        body = "\n".join(current_lines).strip()
        if body:
            turns.append(Turn(speaker=current_speaker.lower(), text=body, index=index))
            index += 1
        current_lines = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        match = SPEAKER_RE.match(line)
        if match:
            flush()
            current_speaker = match.group("speaker").lower()
            current_lines = [match.group("body")]
        else:
            current_lines.append(line)
    flush()

    if not turns:
        turns.append(Turn(speaker="agent", text=text.strip(), index=0))
    return turns


def extract_metadata(text: str) -> dict[str, str]:
    """Read only the leading header block.

    Conversation lines such as ``Agent: I will inspect`` must not overwrite
    ``agent: Codex``.
    """
    meta: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if meta:
                break
            continue
        match = META_RE.match(stripped)
        if not match:
            if meta:
                break
            continue
        key = match.group(1).lower()
        value = match.group(2).strip()
        if key == "agent" and len(value.split()) > 3:
            break
        meta[key] = value
    return meta
