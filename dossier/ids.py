"""Identifier suppression.

Identifiers are for the agent, not the reader. A UUID, a commit hash or a task
key tells a human nothing they can act on, and reading one aloud is thirty
wasted seconds. They stay in the payload so the agent and any tooling can
resolve back to the record; they never reach the page.

Suppression is the default and is applied to every rendered string. It is not a
flag the caller can forget to set.
"""
from __future__ import annotations

import re
from typing import Any

# Ordered: longer/more specific shapes first so a task key is not half-eaten by
# the bare-hex rule.
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("uuid", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)),
    ("task_key", re.compile(r"\btask[-:][0-9a-z_]+(?::[0-9a-f]+)?\b", re.I)),
    ("prefixed_id", re.compile(r"\b(?:project|session|source_event|guidance|msg|run|call)[-:][0-9a-z_]{4,}\b", re.I)),
    ("sha", re.compile(r"\b[0-9a-f]{7,40}\b")),
    ("bearer", re.compile(r"\b(?:sk|gho|ghp|pk)_[A-Za-z0-9_-]{8,}\b")),
]

# Words that look like a hash but are not. Kept visible because a reader acts on
# them: dates, versions, phone numbers, money.
_KEEP = re.compile(r"^(?:\d{4}|\d{1,4}[.]\d|\+?\d[\d\s()-]{6,})$")


def _is_identifier(text: str, kind: str) -> bool:
    if kind != "sha":
        return True
    # A run of digits alone is a count or a year, not a hash.
    return not (text.isdigit() or _KEEP.match(text))


def scrub(value: Any, collected: list[str] | None = None) -> Any:
    """Remove identifiers from anything renderable. Recurses into containers."""
    if isinstance(value, str):
        out = value
        for kind, rx in PATTERNS:
            def _sub(m: re.Match) -> str:
                tok = m.group(0)
                if not _is_identifier(tok, kind):
                    return tok
                if collected is not None:
                    collected.append(tok)
                return ""
            out = rx.sub(_sub, out)
        # tidy the holes left behind: "(  )", " ,", doubled spaces, dangling dashes
        out = re.sub(r"\(\s*\)|\[\s*\]|`\s*`", "", out)
        out = re.sub(r"\s+([,.;:])", r"\1", out)
        out = re.sub(r"[ \t]{2,}", " ", out)
        out = re.sub(r"\s+—\s*$", "", out.rstrip())
        return out.strip()
    if isinstance(value, list):
        return [scrub(v, collected) for v in value]
    if isinstance(value, dict):
        return {k: scrub(v, collected) for k, v in value.items()}
    return value


def find(value: Any) -> list[str]:
    """Identifiers present, without modifying anything. For the stored payload."""
    found: list[str] = []
    scrub(value, found)
    return found
