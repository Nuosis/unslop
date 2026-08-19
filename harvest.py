#!/usr/bin/env python3
"""Harvest real finalization output from agent transcripts.

unslop's own steps 1-2 generate synthetic samples from synthetic prompts. That is
the right default for a domain nobody has produced yet. It is the wrong default
for measuring an agent that has already written thousands of real messages: the
synthetic corpus measures what the model does when asked to perform the domain,
not what it does in production under real pressure.

Every finding that mattered in the first run came from real transcripts -- the
80.7% redundancy rate in particular is invisible in short synthetic samples.

Adapters emit a common record:
    {"id", "source", "project", "session", "ts", "text"}

Usage:
    python3 harvest.py --adapter codex --out unslop-output/samples
    python3 harvest.py --adapter claude-code --since 2026-06-01 --limit 1000
"""
import argparse, hashlib, json, re, sys
from pathlib import Path


# ── shared ────────────────────────────────────────────────────────────────

def _dedupe_key(text):
    return hashlib.sha1(text[:400].encode()).hexdigest()


def _finalizations(turns, min_chars):
    """Given [(role, text, has_tool_call)] in order, yield the assistant messages
    a human actually read: text-only, and last before a human turn or EOF."""
    out = []
    for i, (role, text, tool) in enumerate(turns):
        if role != "assistant" or tool or len(text) < min_chars:
            continue
        nxt = next((turns[j] for j in range(i + 1, len(turns))
                    if turns[j][0] in ("assistant", "user")), None)
        if nxt is not None and nxt[0] != "user":
            continue
        out.append(text)
    return out


# ── Claude Code ───────────────────────────────────────────────────────────

def adapt_claude_code(root, min_chars):
    root = Path(root or Path.home() / ".claude/projects")
    for f in sorted(root.rglob("*.jsonl")):
        turns = []
        for line in f.open(errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("isSidechain") or r.get("isMeta"):
                continue
            t = r.get("type")
            if t not in ("assistant", "user"):
                continue
            c = (r.get("message") or {}).get("content")
            blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c or [])
            if not isinstance(blocks, list):
                continue
            if any(b.get("type") == "tool_result" for b in blocks if isinstance(b, dict)):
                continue  # tool plumbing, not a human turn
            tool = any(b.get("type") == "tool_use" for b in blocks if isinstance(b, dict))
            text = "\n".join(b.get("text", "") for b in blocks
                             if isinstance(b, dict) and b.get("type") == "text").strip()
            turns.append((t, text, tool))
        for text in _finalizations(turns, min_chars):
            yield {"source": "claude-code", "project": f.parent.name,
                   "session": f.stem, "ts": "", "text": text}


# ── Codex ─────────────────────────────────────────────────────────────────

def adapt_codex(root, min_chars):
    root = Path(root or Path.home() / ".codex/sessions")
    for f in sorted(root.rglob("rollout-*.jsonl")):
        turns = []
        first_ts = ""
        cwd = ""
        for line in f.open(errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            p = r.get("payload") or {}
            if r.get("type") == "turn_context" and not cwd:
                cwd = p.get("cwd", "")
            if not first_ts:
                first_ts = r.get("timestamp", "")
            if r.get("type") != "response_item":
                # a tool call between messages marks the assistant as still working
                continue
            pt = p.get("type")
            if pt in ("custom_tool_call", "function_call", "local_shell_call"):
                if turns and turns[-1][0] == "assistant":
                    role, text, _ = turns[-1]
                    turns[-1] = (role, text, True)
                continue
            if pt != "message":
                continue
            role = p.get("role")
            if role not in ("assistant", "user"):
                continue  # developer/system turns are not what a human reads
            c = p.get("content") or []
            text = "".join(b.get("text", "") for b in c
                           if isinstance(b, dict)
                           and b.get("type") in ("output_text", "text", "input_text")).strip()
            turns.append((role, text, False))
        for text in _finalizations(turns, min_chars):
            yield {"source": "codex", "project": (cwd or "?").split("/")[-1] or "~",
                   "session": f.stem[-36:], "ts": first_ts, "text": text}


ADAPTERS = {"claude-code": adapt_claude_code, "codex": adapt_codex}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adapter", required=True, choices=sorted(ADAPTERS))
    ap.add_argument("--root", default=None, help="override the transcript root")
    ap.add_argument("--out", default="unslop-output/samples")
    ap.add_argument("--min-chars", type=int, default=200)
    ap.add_argument("--limit", type=int, default=0, help="cap sample count (0 = all)")
    ap.add_argument("--since", default="", help="ISO date; keep sessions at or after it")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    seen, kept = set(), []
    for rec in ADAPTERS[a.adapter](a.root, a.min_chars):
        if a.since and rec["ts"] and rec["ts"][:10] < a.since:
            continue
        k = _dedupe_key(rec["text"])
        if k in seen:
            continue
        seen.add(k)
        kept.append(rec)

    kept.sort(key=lambda r: r["ts"])
    if a.limit and len(kept) > a.limit:
        step = len(kept) / a.limit           # even spread, not just the newest
        kept = [kept[int(i * step)] for i in range(a.limit)]

    lens = sorted(len(r["text"].split()) for r in kept)
    print(f"adapter={a.adapter}  finalization messages: {len(kept)}")
    if lens:
        print(f"words: median {lens[len(lens)//2]}  p90 {lens[int(.9*len(lens))]}  max {lens[-1]}")
    if a.dry_run or not kept:
        return

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("sample-*.md"):
        p.unlink()
    for i, r in enumerate(kept, 1):
        (out / f"sample-{i:03d}.md").write_text(
            f"<!-- source: {r['source']} | project: {r['project']} | "
            f"session: {r['session'][:8]} | ts: {r['ts']} -->\n\n{r['text']}\n")
    print(f"wrote {len(kept)} samples to {out}")


if __name__ == "__main__":
    main()
