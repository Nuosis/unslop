#!/usr/bin/env python3
"""Stop hook: score Codex's finalization message against the Codex profile.

Mirrors the Claude Code audit, but reads Codex rollout JSONL, whose shape differs:
the final message is a response_item with payload.type=="message", role=="assistant",
content [{type:"output_text"}]. Codex also emits work preambles as assistant
messages, so the finalization is the last one not followed by a tool call.

Writes one JSONL row per turn to ~/.codex/finalization-audit.jsonl.
Never blocks, never prints to the transcript, never raises silently.
"""
import glob, json, os, re, sys

LOG = os.path.expanduser("~/.codex/finalization-audit.jsonl")

COLON_STUB = re.compile(r"^[^\n:]{0,90}:\s*$", re.M)
CERTIFIER = re.compile(r"\b(durable|canonical|authoritative|real|actual|exact)\b", re.I)
BEST_NEXT = re.compile(r"\bbest next step\b|\bnext best step\b", re.I)
NEG_COMPLIANCE = re.compile(
    r"\bI\s+(?:haven't|have not|didn't|did not|won't|will not)\s+\w+"
    r"|\bnothing\s+(?:was|is|has been)\s+\w+"
    r"|\b(?:left|remains?|stays?)\s+(?:untouched|unchanged)\b"
    r"|\bdid not (?:touch|modify|change|push|commit|deploy)\b", re.I)
JARGON = re.compile(r"\b(readback|read-back|the seam|the spine|the shape|the delta|"
                    r"substrate|primitive|surface area|load-bearing)\b", re.I)
DEFN = re.compile(r"(\(|—\s|:\s|,\s)(i\.e\.|that is|meaning|which is)|\bmeans\b", re.I)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crossturn import compare as crossturn_compare
sys.path.insert(0, os.path.expanduser("~/.claude/hooks"))
try:
    from askclass import classify_close, VIOLATIONS   # shared closing classifier
except Exception:
    classify_close, VIOLATIONS = (lambda t: {"close_class": "unknown", "close_ok": True,
                                             "close_why": "", "close_kind": ""}), set()
GATED = {"menu", "handback", "surrender", "continue", "none"}


def final_messages(path, n=2):
    """The last n finalization messages, newest first — cross-turn defects need the
    previous one, which a per-message audit cannot see."""
    out = []
    for t in _all_finals(path)[::-1]:
        out.append(t)
        if len(out) >= n:
            break
    return out


def _all_finals(path):
    turns = []
    with open(path, errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("type") != "response_item":
                continue
            p = r.get("payload") or {}
            pt = p.get("type")
            if pt in ("custom_tool_call", "function_call", "local_shell_call"):
                if turns and turns[-1][0] == "assistant":
                    turns[-1] = ("assistant", turns[-1][1], True)
                continue
            if pt != "message" or p.get("role") not in ("assistant", "user"):
                continue
            txt = "".join(b.get("text", "") for b in (p.get("content") or [])
                          if isinstance(b, dict)
                          and b.get("type") in ("output_text", "text", "input_text")).strip()
            turns.append((p["role"], txt, False))
    return [txt for role, txt, tool in turns
            if role == "assistant" and not tool and len(txt) >= 80]


def final_message(path):
    f = _all_finals(path)
    return f[-1] if f else None


def score(t):
    undef = sum(1 for m in JARGON.finditer(t)
                if not DEFN.search(t[max(0, m.start() - 120): m.end() + 160]))
    v = {
        "words": len(t.split()),
        "colon_stubs": len(COLON_STUB.findall(t)),
        "certifiers": len(CERTIFIER.findall(t)),
        "best_next_step": bool(BEST_NEXT.search(t)),
        "neg_compliance": len(NEG_COMPLIANCE.findall(t)),
        "undefined_jargon": undef,
        # Weak signal only: 4.2% of the corpus against a judged restatement rate of
        # 57.3%. Logged, never gated on, never reported as the redundancy rate --
        # restatement in Codex is distributed prose and no regex reaches it.
        "opener_closer_echo_weak": _echo(t),
    }
    v.update(classify_close(t))
    cls = v["close_class"]
    v["needs_judge"] = cls not in GATED
    # "clean" means "breaks no mechanically-reliable rule", not "good". Restatement,
    # the largest defect at 57.3%, is absent from this gate by design and is supplied
    # by the batch judge.
    v["clean"] = (not (cls in VIOLATIONS and cls in GATED)
                  and v["undefined_jargon"] == 0
                  and v["neg_compliance"] == 0)
    return v


def _echo(t):
    sents = [s for s in re.split(r"(?<=[.!?])\s+", t.strip()) if len(s.split()) > 4]
    if len(sents) < 3:
        return False
    def words(s):
        return {w for w in re.findall(r"[a-z]{4,}", s.lower())}
    a, b = words(sents[0]), words(sents[-1])
    return bool(a and b and len(a & b) / min(len(a), len(b)) >= 0.5)


STATE = os.path.expanduser("~/.codex/hooks/state-finalization")


def _prev_path(sid):
    return os.path.join(STATE, f"{sid or 'unknown'}.txt")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    # Codex hands the Stop hook the message directly. It does NOT pass a transcript
    # path -- confirmed from the payload alignment_guard.py already consumes. Reading
    # it here avoids globbing 14,992 rollout files on every turn.
    t = (payload.get("last_assistant_message") or "").strip()
    sid = payload.get("session_id") or ""

    # transcript_path is honoured when present (backfill/testing passes one)
    path = payload.get("transcript_path") or payload.get("rollout_path")
    prev = None
    if not t and path and os.path.exists(path):
        msgs = final_messages(path, 2)
        t = msgs[0] if msgs else None
        prev = msgs[1] if len(msgs) > 1 else None
    elif t:
        # previous finalization is kept per-session, mirroring alignment_guard's state
        try:
            with open(_prev_path(sid)) as fh:
                prev = fh.read()
        except Exception:
            prev = None

    if t and len(t) >= 80:
        try:
            if True:
                import hashlib
                row = {"harness": "codex",
                       "session": sid,
                       "cwd": payload.get("cwd", ""),
                       "turn": payload.get("turn_id", ""),
                       "transcript": path,
                       "msg_sha": hashlib.sha1(t.encode()).hexdigest()[:12]}
                row.update(score(t))
                # log-only: 68% precision / 85% recall against a judge; a screen for
                # the batch judge, never a verdict
                ct = crossturn_compare(t, prev)
                row["carried_from_prev_weak"] = ct["carried_units"]
                row["neg_restated_weak"] = ct["neg_restated"]
                row["has_prev"] = ct["has_prev"]
                if ct["carried_units"] or ct["neg_restated"]:
                    row["needs_judge"] = True
                with open(LOG, "a") as fh:
                    fh.write(json.dumps(row) + "\n")
                os.makedirs(STATE, exist_ok=True)
                with open(_prev_path(sid), "w") as fh:
                    fh.write(t)
        except Exception:
            import traceback
            with open(LOG + ".err", "a") as fh:
                fh.write(traceback.format_exc() + "\n")
    print(json.dumps({"suppressOutput": True}))


if __name__ == "__main__":
    main()
