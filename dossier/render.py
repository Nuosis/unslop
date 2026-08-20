"""Compose a dossier document from agent-supplied data.

The agent supplies data and never names an element or writes markup. This is the
line that separates this from a component registry, where the agent picks a
widget per call and composes the page itself, one turn at a time.
"""
from __future__ import annotations

import json
from html import escape
from typing import Any

from .elements import RENDERERS, el_unknown
from .ids import find
from .theme import CSS

# No external requests: no fonts, no scripts, no images. Renders identically
# offline and gives the served page nothing to exfiltrate with.
CSP = ("default-src 'none'; style-src 'unsafe-inline'; img-src data:; "
       "form-action 'none'; base-uri 'none'; frame-ancestors 'self'")


def render(doc: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Return (html, meta). meta carries the identifiers stripped from the page
    so the agent can still resolve records; they are never rendered."""
    body, shapes = [], []
    for s in doc.get("sections", []) or []:
        if not isinstance(s, dict):
            continue
        kind = str(s.get("type", "")).lower()
        fn = RENDERERS.get(kind)
        if fn is None:
            shapes.append(kind or "untyped")
        body.append((fn or el_unknown)(s))

    title = escape(str(doc.get("title") or "Dossier"))
    summary = doc.get("summary")
    sum_html = f"<p class='sum'>{escape(str(summary))}</p>" if summary else ""
    stamp = escape(str(doc.get("stamp") or ""))

    html = (
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<meta http-equiv='Content-Security-Policy' content=\"{CSP}\">"
        f"<meta name='referrer' content='no-referrer'>"
        f"<title>{title}</title><style>{CSS}</style></head><body><div class='wrap'>"
        f"<h1>{title}</h1>{sum_html}{''.join(body)}"
        + (f"<p class='stamp'>{stamp}</p>" if stamp else "")
        + "</div></body></html>")

    return html, {
        # identifiers live here, for the agent; the page never shows them
        "identifiers": sorted(set(find(doc))),
        # shapes no element covers yet -- promote at three uses, not on a guess
        "unknown_shapes": shapes,
        "sections": len(body),
    }
