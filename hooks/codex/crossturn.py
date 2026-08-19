"""Compare a finalization message against the one before it in the same session.

The per-message audit cannot see this class of defect at all: a claim repeated from
last turn is lexically identical to a claim made once. Measured across 817 consecutive
pairs, 44.6% carry content forward unchanged (2.02 repeated units per affected pair).

Two signals:
  carried_units   - sentences whose content already appeared in the previous message
  neg_restated    - a non-action claim ("I haven't touched X") the previous message
                    already made, repeated as standing compliance
"""
import re

NEG = re.compile(
    r"(\bI\s+(?:haven't|have not|didn't|did not|won't|will not|am not)\s+[\w\s]{0,30}"
    r"|\bnothing\s+(?:was|is|has been)\s+\w+"
    r"|\b(?:left|remains?|stays?)\s+(?:untouched|unchanged)"
    r"|\bdid not (?:touch|modify|change|push|commit|deploy)[\w\s]{0,20})", re.I)

# Content words only. Identifiers and numbers are excluded from the overlap test:
# repeating a SHA or a test count across turns is often load-bearing, and the
# profile protects it -- the defect is repeating the prose claim around it.
STOP = {"that","this","with","from","have","been","they","them","were","will",
        "your","yours","what","when","then","than","into","only","also","just",
        "does","done","which","there","here","because","after","before","would"}


def _sentences(t):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", t) if len(s.split()) >= 6]


def _content(s):
    return frozenset(w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in STOP)


def compare(current, previous, threshold=0.6):
    if not previous:
        return {"carried_units": 0, "neg_restated": 0, "has_prev": False}
    prev = [c for c in (_content(s) for s in _sentences(previous)) if len(c) >= 5]
    carried = 0
    for s in _sentences(current):
        n = _content(s)
        if len(n) < 5:
            continue
        if any(len(n & p) / min(len(n), len(p)) >= threshold for p in prev):
            carried += 1

    def claims(t):
        return {frozenset(m.group(0).lower().split()) for m in NEG.finditer(t)}
    a, b = claims(previous), claims(current)
    neg = sum(1 for x in b
              if any(len(x & y) / max(1, min(len(x), len(y))) >= 0.6 for y in a))
    return {"carried_units": carried, "neg_restated": neg, "has_prev": True}
