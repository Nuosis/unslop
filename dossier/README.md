# Dossier

Claire dumps data. This renders it. She never names an element or writes markup —
that is the line between this and a component registry, where the agent picks a
widget per call and composes the page itself.

## Elements

Derived by counting what she actually conveyed across 44 real messages:

| element | how often she needed it |
|---|---|
| `list` | 63.6% |
| `record` | 52.3% |
| `timeline` | 25.0% |
| `status_table` | 20.5% |
| `decision` | 11.4% |
| `metric` | 6.8% |

No code block (0 of 44). No chart — metrics appear in 6.8% and never as a
repeated series, so the timeline covers what the data actually holds.

An unrecognised shape still renders, and is logged in `meta.unknown_shapes`.
Promote one to a real element at three uses, not on a guess — that is what keeps
six elements from becoming forty.

## Identifiers are never rendered

UUIDs, commit hashes, task keys and session ids are for the agent. A reader
cannot act on one. They are stripped from every rendered string and returned in
`meta.identifiers`, so records stay resolvable without putting noise on the page.

Kept visible, because a reader acts on them: dates, money, counts, phone
numbers, version strings, times.

This pairs with the voice rule "speak the name, keep the id" — the id is kept in
the record, not on the page and not in the air.

## Safety

The agent supplies values into fixed markup, never markup. Values are scrubbed,
then escaped. The page makes no external request — no fonts, no scripts, no
images — and ships a `default-src 'none'` policy. Serve it from a separate
hostname in a sandboxed frame so agent output never runs against admin cookies.

## Lifecycle

A dossier belongs to a session and is deleted when that session resets. `pinned`
survives. Orphans expire after 48 hours.
