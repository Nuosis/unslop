#!/usr/bin/env python3
"""Batch redundancy judge over the finalization audit log.

Conceptual redundancy — a message restating something it already said — is the
largest measured defect (80.7% of the 803-message baseline, 2.09 restated points
each). No regex finds it: it is distributed prose restatement, not a labelled
recap section (that shape is only 1.1%). So it is judged, in batch, offline.

Run manually or on a schedule. It is NOT a per-turn hook: Stop hooks only accept
command hooks, and a per-turn LLM call would add latency to every turn.

  python3 ~/.claude/hooks/finalization-judge.py [--last N]
"""
import argparse, json, os, re, subprocess, sys, tempfile

LOG = os.path.expanduser("~/.claude/finalization-audit.jsonl")
OUT = os.path.expanduser("~/.claude/finalization-redundancy.jsonl")


def blocks(rec):
    m = rec.get("message") or {}
    c = m.get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return c if isinstance(c, list) else []


def retrieve(transcript, sha):
    """Pull the exact message this row scored, by its content hash."""
    import hashlib
    if not transcript or not os.path.exists(transcript):
        return None
    with open(transcript, errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("type") != "assistant" or r.get("isSidechain"):
                continue
            b = blocks(r)
            if not b or any(x.get("type") == "tool_use" for x in b):
                continue
            t = "\n".join(x.get("text", "") for x in b if x.get("type") == "text").strip()
            if hashlib.sha1(t.encode()).hexdigest()[:12] == sha:
                return t
    return None


def _previous_of(transcript, sha):
    """The finalization message immediately before the one with this hash."""
    import hashlib
    seen = []
    if not os.path.exists(transcript):
        return None
    with open(transcript, errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("type") != "assistant" or r.get("isSidechain"):
                continue
            b = blocks(r)
            if not b or any(x.get("type") == "tool_use" for x in b):
                continue
            t = "\n".join(x.get("text", "") for x in b if x.get("type") == "text").strip()
            if len(t) < 80:
                continue
            if hashlib.sha1(t.encode()).hexdigest()[:12] == sha:
                return seen[-1] if seen else None
            seen.append(t)
    return None


PROMPT = """Read every file in this directory named msg-*.txt, in full.

Each is one final assistant message from a coding session. Judge each for CONCEPTUAL
REDUNDANCY — the message restating something it already said, in different words. Not
verbatim repetition. Look for: a summary or scorecard recapping the body; the same fact
given once as prose and again as a bullet or table cell; circling back to re-explain;
a closing paragraph that recaps rather than adds; the same caveat stated twice.

A heading that labels a section is not redundancy. A number repeated because it is
load-bearing in two different claims is not redundancy. Restating the same claim so the
reader reads it twice IS redundancy.

Some files contain a PREVIOUS MESSAGE section before the current one. Where present,
also judge CROSS-TURN REPETITION: does the current message restate a fact, status,
caveat, blocker or conclusion the reader was already told last turn, when nothing
about it materially changed? A changed count, a flipped state, or a brief reference
made in order to build on it is NOT repetition. Repeating a non-action claim ("I
haven't touched X", "nothing is committed") the previous message already made is
repetition, and is the standing-compliance defect specifically.

Then judge how each message ENDS. The user's standing instructions: make the call and
act; never ask when the answer is derivable from context, repo, git or memory; if you
must ask, lead with the recommendation, never a neutral menu; never ask permission to
continue authorised work.

- BLOCKED: genuinely cannot proceed — lacks a credential or access not on this machine,
  the next action is irreversible or reaches a real person, it needs an action only the
  user can take (his browser, account, money, device), a fact only he holds, or it would
  touch someone else's uncommitted work or live data. Correct.
- REDIRECT: stated a decision with a reason, then a short line inviting override. Correct.
- NOTHING: the ending asks and offers nothing. Correct.
- HANDBACK / MENU / SURRENDER / CONTINUE: violations, as the user defines them above.

Judge what the ending does, not how it is worded. An ask naming a specific missing
credential is BLOCKED even if phrased "want me to". An offer with no blocker is
HANDBACK however politely worded. Two agent actions offered as a choice is MENU even
if a blocker is mentioned elsewhere.

Output one tab-separated line per file, nothing else, to ./verdict.tsv:
<filename>\tREDUNDANT|CLEAN\t<restated point count>\t<clearest restatement>\t<BLOCKED|REDIRECT|NOTHING|HANDBACK|MENU|SURRENDER|CONTINUE>\t<one-line reason quoting the ending>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=int, default=50, help="judge the N most recent rows")
    args = ap.parse_args()

    if not os.path.exists(LOG):
        print(f"no audit log at {LOG}", file=sys.stderr)
        return 1
    rows = [json.loads(l) for l in open(LOG) if l.strip()][-args.last:]

    with tempfile.TemporaryDirectory() as d:
        idx = {}
        for i, r in enumerate(rows, 1):
            t = retrieve(r.get("transcript"), r.get("msg_sha", ""))
            if not t:
                continue
            name = f"msg-{i:03d}.txt"
            body = t
            if r.get("has_prev") and r.get("transcript"):
                prev = _previous_of(r["transcript"], r.get("msg_sha", ""))
                if prev:
                    body = f"## PREVIOUS MESSAGE\n\n{prev}\n\n---\n\n## THIS MESSAGE\n\n{t}"
            open(os.path.join(d, name), "w").write(body)
            idx[name] = r
        if not idx:
            print("no messages could be retrieved (transcripts rotated?)", file=sys.stderr)
            return 1
        print(f"judging {len(idx)} messages...", file=sys.stderr)
        subprocess.run(["claude", "-p", "--permission-mode", "acceptEdits", PROMPT],
                       cwd=d, capture_output=True, timeout=1800)
        vpath = os.path.join(d, "verdict.tsv")
        if not os.path.exists(vpath):
            print("judge produced no verdict.tsv", file=sys.stderr)
            return 1
        n = red = pts = 0
        with open(OUT, "a") as out:
            for line in open(vpath):
                f = line.rstrip("\n").split("\t")
                if len(f) < 3 or f[0] not in idx:
                    continue
                n += 1
                r = dict(idx[f[0]])
                r["redundant"] = f[1].strip().upper().startswith("REDUND")
                r["restated_points"] = int(f[2]) if f[2].strip().isdigit() else 0
                r["example"] = f[3] if len(f) > 3 else ""
                if len(f) > 6:
                    r["cross_turn"] = f[6].strip().lower()
                    r["cross_turn_why"] = f[7] if len(f) > 7 else ""
                if len(f) > 4:
                    r["close_judged"] = f[4].strip().lower()
                    r["close_judged_ok"] = r["close_judged"] in (
                        "blocked", "redirect", "nothing")
                    r["close_judged_why"] = f[5] if len(f) > 5 else ""
                    # the structural pass defers on "blocked"; record when the judge
                    # overturns it so the classifier's error rate stays visible
                    r["judge_overturned"] = (
                        r.get("close_class") in ("blocked", "redirect", "async-note")
                        and not r["close_judged_ok"])
                red += r["redundant"]
                pts += r["restated_points"]
                out.write(json.dumps(r) + "\n")
    if n:
        print(f"redundant: {red}/{n} = {100*red/n:.1f}%  ({pts} restated points)")
        print(f"baseline to beat: 80.7% redundant / 2.09 per message; 34.7% bad close")
        print(f"appended to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
