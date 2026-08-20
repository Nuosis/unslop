"""The six elements, derived by counting what Claire actually conveyed across
her 44 real messages:

    list          63.6%      record        52.3%
    timeline      25.0%      status_table  20.5%
    decision      11.4%      metric         6.8%

A code block appeared in 0 of 44 and is deliberately absent. A chart appeared as
a repeated numeric series in none of them; the timeline covers what she had.

Every element renders values into fixed markup. The caller supplies data, never
markup, so agent output cannot carry script or break the theme.
"""
from __future__ import annotations

from html import escape
from typing import Any

from .ids import scrub

STATUS = {
    "done": ("ok", "done"), "green": ("ok", "done"), "complete": ("ok", "done"),
    "open": ("warn", "open"), "pending": ("warn", "pending"), "waiting": ("warn", "waiting"),
    "blocked": ("bad", "blocked"), "failed": ("bad", "failed"), "error": ("bad", "failed"),
}


def _t(v: Any) -> str:
    """Scrub identifiers, then escape. Order matters: scrub the raw value so the
    patterns see real text, escape after so nothing executes."""
    return escape(scrub("" if v is None else str(v)))


def _heading(s: dict) -> str:
    h = s.get("heading")
    return f"<h2>{_t(h)}</h2>" if h else ""


def el_list(s: dict) -> str:
    items = "".join(f"<li>{_t(i)}</li>" for i in s.get("items", []) if str(i).strip())
    return f"<section class='el list'>{_heading(s)}<ul>{items}</ul></section>"


def el_record(s: dict) -> str:
    rows = "".join(
        f"<div class='f'><dt>{_t(k)}</dt><dd>{_t(v)}</dd></div>"
        for k, v in (s.get("fields") or {}).items() if str(v).strip())
    return f"<section class='el record'>{_heading(s)}<dl>{rows}</dl></section>"


def el_timeline(s: dict) -> str:
    ev = "".join(
        f"<li><span class='when'>{_t(e.get('when'))}</span>"
        f"<span class='what'>{_t(e.get('what'))}</span></li>"
        for e in s.get("events", []))
    return f"<section class='el timeline'>{_heading(s)}<ol>{ev}</ol></section>"


def el_status_table(s: dict) -> str:
    head = "".join(f"<th>{_t(c)}</th>" for c in s.get("columns", ["", "Status", ""]))
    body = []
    for r in s.get("rows", []):
        cls, label = STATUS.get(str(r.get("status", "")).lower(), ("neutral", r.get("status", "")))
        body.append(
            f"<tr><td>{_t(r.get('label'))}</td>"
            f"<td><span class='pill {cls}'>{_t(label)}</span></td>"
            f"<td>{_t(r.get('detail'))}</td></tr>")
    return (f"<section class='el table'>{_heading(s)}<div class='scroll'><table>"
            f"<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>")


def el_decision(s: dict) -> str:
    opts = []
    for o in s.get("options", []):
        rec = " rec" if o.get("recommended") else ""
        tag = "<span class='tag'>recommended</span>" if o.get("recommended") else ""
        opts.append(f"<li class='opt{rec}'><span class='name'>{_t(o.get('name'))}</span>{tag}"
                    f"<span class='detail'>{_t(o.get('detail'))}</span></li>")
    q = f"<p class='q'>{_t(s.get('question'))}</p>" if s.get("question") else ""
    return f"<section class='el decision'>{_heading(s)}{q}<ul>{''.join(opts)}</ul></section>"


def el_metric(s: dict) -> str:
    m = "".join(
        f"<div class='m'><span class='v'>{_t(x.get('value'))}</span>"
        f"<span class='l'>{_t(x.get('label'))}</span>"
        + (f"<span class='n'>{_t(x.get('note'))}</span>" if x.get("note") else "")
        + "</div>"
        for x in s.get("metrics", []))
    return f"<section class='el metrics'>{_heading(s)}<div class='row'>{m}</div></section>"


def el_unknown(s: dict) -> str:
    """A shape no renderer covers yet. Rendered rather than dropped, and logged
    so a shape that recurs can be promoted to a real element instead of the set
    growing by guesswork."""
    body = "".join(f"<div class='f'><dt>{_t(k)}</dt><dd>{_t(v)}</dd></div>"
                   for k, v in s.items() if k not in ("type", "heading"))
    return (f"<section class='el record unknown' data-shape='{_t(s.get('type'))}'>"
            f"{_heading(s)}<dl>{body}</dl></section>")


RENDERERS = {
    "list": el_list, "record": el_record, "timeline": el_timeline,
    "status_table": el_status_table, "decision": el_decision, "metric": el_metric,
}
