#!/usr/bin/env python3
"""Stop hook: score the turn's final message against the finalization profile.

Writes one JSONL row per turn to ~/.claude/finalization-audit.jsonl.
Never blocks, never prints to the transcript, never raises.
"""
import json, re, sys, glob, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from askclass import classify_close, VIOLATIONS

# Categories the structural pass calls correctly at >=91% against an LLM judge on 86
# stratified cases. "blocked" is deliberately NOT here: it scored 83%, and it is the
# category that EXCUSES an ask, so a wrong call there lets a real handback through.
# It is routed to the judge instead. Violations gate; excuses are judged.
GATED = {"menu", "handback", "surrender", "continue", "none"}

LOG = os.path.expanduser("~/.claude/finalization-audit.jsonl")

# Rules that map to a standing directive. Violations are the compliance metric.
JARGON = re.compile(
    r"\b(the seam|the spine|the gate|the fork|the tell|the delta|the shape|the loop|"
    r"load-bearing|split-brain|false green|hollow completion|substrate|primitive|"
    r"surface area|blast radius|affordance|long pole)\b", re.I)
DEFN = re.compile(r"(\(|—\s|:\s|,\s)(i\.e\.|that is|meaning|which is)|\bmeans\b", re.I)
SELF_CERT = re.compile(r"\b(honest|actually|exactly|genuinely|deliberately|plainly)\b", re.I)
ANTITHESIS = re.compile(r",\s+not\s+\b\w+|\brather than\b", re.I)
COUNTED = re.compile(r"\b(Two|Three|Both)\s+(things|decisions|caveats|notes|options|ways|gaps|flags)\b", re.I)

# Reporting what was NOT done. 26.8% of the 803-message corpus, 265 instances.
NEG_COMPLIANCE = re.compile(r"""(
 \bI\s+(?:haven't|have\s+not|didn't|did\s+not|won't|will\s+not|am\s+not|never)\s+\w+
|\bnothing\s+(?:was|is|has\s+been|got)\s+\w+
|\bno\s+(?:changes?|commits?|files?|code|migrations?|deploys?)\s+(?:were|was|have|has)\b
|\b(?:left|remains?|stays?)\s+(?:untouched|unchanged|as[- ]is)\b
|\bdid\s+not\s+(?:touch|modify|change|alter|delete|remove|push|commit|deploy)\b
|\bwithout\s+(?:touching|modifying|changing|altering)\b
|\bas\s+you\s+(?:asked|said|instructed),?\s+I\s+(?:didn't|did\s+not|haven't)\b
)""", re.I | re.X)

# Weak signal only. Conceptual redundancy runs at 80.7% (judged), but it is distributed
# prose restatement, not a labelled recap section: this regex finds 1.1% of the corpus.
# It is logged, never gated on, and never reported as the redundancy rate. Redundancy is
# measured by finalization-judge.py, which batches an LLM judge over these rows offline.
RECAP_BLOCK = re.compile(
    r"^#{1,4}\s*(?:the\s+)?(?:full\s+)?(?:net|summary|recap|scorecard|state|status|"
    r"where\s+(?:things\s+stand|we\s+are)|current\s+state|the\s+full\s+picture)\b",
    re.I | re.M)


def blocks(rec):
    m = rec.get("message") or {}
    c = m.get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return c if isinstance(c, list) else []


def find_final_message(path):
    recs = []
    with open(path, errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except Exception:
                continue
    for r in reversed(recs):
        if r.get("type") != "assistant" or r.get("isSidechain"):
            continue
        b = blocks(r)
        if not b or any(x.get("type") == "tool_use" for x in b):
            continue
        t = "\n".join(x.get("text", "") for x in b if x.get("type") == "text").strip()
        if len(t) >= 80:
            return t
    return None


def score(t):
    undefined = 0
    for m in JARGON.finditer(t):
        ctx = t[max(0, m.start() - 120):m.end() + 160]
        if not DEFN.search(ctx):
            undefined += 1
    words = len(t.split())
    v = {
        "words": words,
        **classify_close(t),
        "undefined_jargon": undefined,
        "self_cert": len(SELF_CERT.findall(t)),
        "antithesis": len(ANTITHESIS.findall(t)),
        "counted_preamble": len(COUNTED.findall(t)),
        "neg_compliance": len(NEG_COMPLIANCE.findall(t)),
        "recap_header_weak": bool(RECAP_BLOCK.search(t[len(t) // 2:])),
        "em_dash": t.count("—"),
        "bold": len(re.findall(r"\*\*[^*\n]+\*\*", t)),
        "arrow": t.count("→"),
    }
    # A turn is "clean" if it breaks none of the mechanically-checkable hard rules.
    # Word count is logged as a trend, never gated on: an arbitrary cut-off cuts a
    # message that earned its length and passes a short one that repeats itself.
    # Conceptual redundancy is the largest defect (80.7%) and is NOT represented here:
    # no regex finds it. "clean" therefore means "breaks no mechanical rule", not
    # "good". finalization-judge.py supplies the redundancy verdict separately.
    cls = v["close_class"]
    v["needs_judge"] = cls not in GATED
    v["clean"] = (
        not (cls in VIOLATIONS and cls in GATED)
        and v["undefined_jargon"] == 0
        and v["neg_compliance"] == 0
    )
    return v


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    path = payload.get("transcript_path")
    if not path or not os.path.exists(path):
        sid = payload.get("session_id", "")
        hits = glob.glob(os.path.expanduser(f"~/.claude/projects/**/{sid}.jsonl"), recursive=True) if sid else []
        path = hits[0] if hits else None
    if path and os.path.exists(path):
        try:
            t = find_final_message(path)
            if t:
                import hashlib
                row = {
                    "session": payload.get("session_id", ""),
                    "cwd": payload.get("cwd", ""),
                    "transcript": path,
                    "msg_sha": hashlib.sha1(t.encode()).hexdigest()[:12],
                }
                row.update(score(t))
                with open(LOG, "a") as fh:
                    fh.write(json.dumps(row) + "\n")
        except Exception:
            # never block the turn, but never silently swallow either
            import traceback
            with open(LOG + ".err", "a") as fh:
                fh.write(traceback.format_exc() + "\n")
    print(json.dumps({"suppressOutput": True}))


if __name__ == "__main__":
    main()
