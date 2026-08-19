"""Classify how a finalization message hands control back.

v2. v1 scored 64% agreement against an LLM judge on 86 stratified cases; every
systematic miss was the same shape -- it only knew about blockers on THIS machine
(a missing token) and not about blockers in the user's world: an action only he can
perform, a fact only he holds, someone else's in-flight work, or an outbound action
that reaches a real person.

This layer decides only what is structurally decidable. Whether an ask is genuinely
unavoidable is intent, and intent is judged in the batch pass, not matched here.
"""
import re

X = re.I | re.X

# ── does the ending ask or offer at all ────────────────────────────────────
OFFER = re.compile(r"""(
 \bwant\s+me\s+to\b | \bshall\s+I\b | \bshould\s+I\b | \bdo\s+you\s+want\b
|\bsay\s+the\s+word\b | \bjust\s+say\b | \blet\s+me\s+know\b | \byour\s+call\b
|\bI\s+can\s+(?:also\s+)?(?:do|run|build|add|take|write|wire|start|commit)\b
|\bhappy\s+to\b | \bif\s+you(?:'d)?\s+(?:want|like|prefer|rather)\b
|\btell\s+me\b | \bsend\s+(?:me\s+)?the\b | \bconfirm\b
|\bpoint\s+me\s+at\b | \bsay\s+which\b | \bsay\s+go\b | \bgive\s+me\s+the\b
|\bwhich\s+of\s+those\b | \bhow\s+do\s+you\s+want\b | \byour\s+shout\b
)""", X)

# ── async status note: reporting a background result, not requesting anything ──
ASYNC_NOTE = re.compile(r"""(
 \bI'?ll\s+(?:report|update\s+you|come\s+back|post|flag)\b[^.\n]{0,60}
  \b(?:when|once|as\s+soon\s+as|after)\b
|\bwaiting\s+on\b[^.\n]{0,50}\b(?:build|deploy|run|CI|converge)
)""", X)
IN_FLIGHT = re.compile(r"""(
 \b(?:is|are)\s+(?:in\s+flight|running|building|deploying|underway|queued)\b
|\bkicked\s+off\b | \bstarted\s+(?:the\s+)?(?:build|run|deploy)\b
|\bin\s+the\s+background\b | \bre-?run\b[^.\n]{0,30}\bin\s+flight\b
)""", X)

# ── blockers: things the agent cannot do or must not decide ────────────────
# A. no access on this machine
B_ACCESS = re.compile(r"""(
 \bno\s+(?:\w+\s+){0,2}(?:token|credential|key|password|secret|access|account|permission)\b
|\b(?:token|credential|key|api\s*key)\b[^.\n]{0,30}\b(?:not\s+set|isn'?t\s+set|not\s+configured|not\s+available)\b
|\bI\s+(?:don'?t|do\s+not)\s+have\b | \bI\s+can(?:'?t|not)\s+(?:derive|reach|access|get|obtain|see)\b
|\bnot\s+(?:configured|on\s+this\s+machine|available\s+here)\b
|\bneeds?\s+(?:the\s+)?[\w\s]{0,20}credentials\b
)""", X)
# B. only the user can perform it (his browser, his account, his money, his device)
B_USER_ACTION = re.compile(r"""(
 \brun\s+(?:it|that|this)\s+yourself\b | \byou'?ll\s+need\s+to\b | \byou\s+(?:have\s+to|must)\b
|\b(?:go|head)\s+(?:back\s+)?to\s+(?:that|the)\s+\w+\s*(?:screen|console|dashboard|page|portal)\b
|\bin\s+your\s+browser\b | \bneeds?\s+your\s+browser\b
|\bclick\s+['"‘’]?\w | \bsign\s+in\s+(?:to|at)\b | \blog\s+in\s+(?:to|at)\b
|\b(?:buy|purchase|pay\s+for|subscribe)\b
|\binstall\s+the\s+\w+\s+app\b | \bauthori[sz]e\s+the\b
|\btell\s+me\s+when\s+(?:it'?s|you'?ve|that'?s)\b
|\bgcloud\s+auth\s+login\b | \bthat\s+step\s+needs\s+your\b
)""", X)
# C. irreversible or outward-facing
B_IRREVERSIBLE = re.compile(r"""(
 \bis\s+irreversible\b | \bcan'?t\s+be\s+(?:undone|reverted|rolled\s+back)\b
|\bdestructive\b | \bforce[-\s]push\b | \bdelete\s+(?:the|those|that)\b
|\b(?:text|SMS|email|mail)s?\b[^.\n]{0,40}\b(?:a\s+)?(?:real\s+person|customer|client|cell|mobile|Lance|Liz)\b
|\bsurprise\s+a\s+real\s+person\b | \boutbound\b[^.\n]{0,30}\b(?:SMS|mail|email)\b
|\bsend(?:ing)?\s+(?:customer|client|real)\s+mail\b
|\blive\s+writes?\s+to\s+your\b | \blive\s+(?:prod|production|customer)\s+data\b
|\bcosts?\s+(?:money|real\s+money|provider\s+tokens)\b | \bcharges?\s+(?:the|a)\s+card\b
)""", X)
# D. someone else's property or in-flight work
B_NOT_MINE = re.compile(r"""(
 \b(?:someone\s+else'?s|isn'?t\s+mine|not\s+mine|another\s+(?:person|team|session))\b
|\buncommitted\s+work\b | \bin-?flight\s+work\b | \bparallel\s+session\b
|\bshared\s+tree\b | \byours\s+or\s+\w+'?s\b | \bwork\s+I\s+didn'?t\s+create\b
)""", X)
# E. a fact only the user holds
B_USER_FACT = re.compile(r"""(
 \byour\s+(?:mobile|phone|cell)\s+number\b | \bwon'?t\s+guess\s+a\s+\w+\s+number\b
|\bwhat'?s\s+\w+'?s\s+(?:actual\s+)?(?:request|ask|intent)\b
|\bonly\s+you\s+(?:know|can\s+say)\b | \bI\s+can'?t\s+know\b
)""", X)
# Strong blockers are unambiguous wherever they appear: naming one of these means
# the agent genuinely cannot proceed. Weak blockers ("not mine", "I don't have") are
# ordinary phrases that only count as a constraint when stated in the ask itself.
B_STRONG_EXTRA = re.compile(r"""(
 \bgcloud\s+auth\s+login\b | \bneeds?\s+your\s+browser\b | \brun\s+it\s+yourself\b
|\b(?:buy|purchase|pay\s+for)\b[^.\n]{0,40}\b(?:mailbox|licence|license|seat|plan|domain)\b
|\bapprove[-\s]and[-\s]send\b | \bsend(?:ing)?\b[^.\n]{0,30}\bto\s+(?:Lance|Liz|the\s+customer|the\s+client)\b
|\breachable\s+from\s+outside\b | \bon-?LAN\b | \bnetwork\s+topology\b
|\bwhat'?s\s+\w+'?s\s+(?:actual\s+)?(?:request|ask)\b | \bis\s+she\s+confirming\b
|\bonly\s+you\s+can\b | \bthat\s+step\s+needs\s+your\b
|\bfrom\s+a\s+source\s+I\s+can'?t\s+account\s+for\b
)""", X)
STRONG = [("user-action", B_USER_ACTION), ("irreversible", B_IRREVERSIBLE),
          ("strong-extra", B_STRONG_EXTRA)]
WEAK = [("access", B_ACCESS), ("not-mine", B_NOT_MINE), ("user-fact", B_USER_FACT)]

# ── a decision actually taken in this message ─────────────────────────────
DECISION = re.compile(r"""(
 \bI'?m\s+(?:going\s+with|taking|starting|doing|building|using|shipping)\b
|\bI'?d\s+(?:take|go\s+with|use|pick|start|build)\b | \bgoing\s+with\b | \bmy\s+pick\s+is\b
|\bI'?ll\s+(?:build|do|wire|take|start|run)\s+\w+\s+(?:next|first|that\s+way)\b
|^\s*(?:Starting|Building|Running|Doing|Taking|Shipping|Deploying)\b
|\bthe\s+next\s+step\s+is\b | \bthat'?s\s+what\s+I'?ll\s+build\s+first\b
|\bso\s+that'?s\s+what\s+I'?ll\b
)""", X | re.M)

REDIRECT = re.compile(r"""^(?:say|tell\s+me|shout|override|push\s+back|correct\s+me)\b.{0,110}?
 (?:if\s+you(?:'d|\s+would)?\s+(?:rather|prefer|want)|otherwise|instead|if\s+that'?s\s+wrong)""", X | re.S)
# "...unless you want X first" -- a decision plus an override, inline
UNLESS = re.compile(r"\bunless\s+you\s+(?:want|"r"'?d\s+rather|prefer)\b", re.I)

SURRENDER = re.compile(r"""(
 \b(?:but|though|that\s+said)[^.\n]{0,60}\b(?:your\s+call|up\s+to\s+you|your\s+decision)\b
|\byour\s+call\b | \bup\s+to\s+you\b | \byour\s+(?:judgment|shout)\b
|\bwhichever\s+you\s+(?:prefer|want)\b | \btell\s+me\s+which\b
|\bmy\s+default\s+is\b[^.\n]{0,60}\btell\s+me\b
)""", X)
MENU = re.compile(r"""(
 \bwhich\s+(?:way|one|direction|option|do\s+you)\b[^.\n]{0,70}\?
|\bwant\s+me\s+to\b[^?\n]{0,110}\bor\b[^?\n]{0,110}\?
|\bdo\s+you\s+want\b[^?\n]{0,100}\bor\b[^?\n]{0,100}\?
|\btell\s+me\s+whether\s+you\s+want\b[^.\n]{0,90}\bor\b
|\bA,?\s+or\s+B\b
|\bhow\s+do\s+you\s+want\s+to\s+proceed\b
|\bsay\s+which\s+of\s+(?:those|these)\b | \bwhich\s+of\s+(?:those|these)\b
|\bpoint\s+me\s+at\b[^.\n]{0,90}\bor\s+say\b
|\beither\b[^?\n]{0,80}\bor\b[^?\n]{0,80}\?
)""", X)
# Two agent actions offered as a choice. This is a violation even when a real blocker
# is present elsewhere: asking how to resolve a constraint is legitimate, handing over
# a pick between two things you could go build is not.
WORK_MENU = re.compile(r"""
 \b(?:want\s+me\s+to|should\s+I|do\s+you\s+want\s+me\s+to)\b
 [^?\n]{0,120}?\b(?:or)\b[^?\n]{0,120}?
 \b(?:build|wire|dig|keep|run|add|take|deploy|backfill|tune|push|write|start|pull|land|do)\b
 [^?\n]{0,80}\?
|\bhow\s+do\s+you\s+want\s+to\s+proceed\b
|\bwhich\s+(?:lane|way|one|option)\b[^.\n]{0,80}(?:\?|—)
""", X)

CONTINUE = re.compile(
    r"\b(?:want\s+me\s+to\s+)?(?:keep\s+going|continue|carry\s+on|proceed|press\s+on)\b[^.\n]{0,40}\?", re.I)

VIOLATIONS = {"handback", "menu", "surrender", "continue"}


def final_sentence(t):
    parts = re.split(r"(?<=[.!?])\s+", t.rstrip())
    return parts[-1].strip() if parts else ""


def classify_close(text):
    t = text.rstrip()
    close = t[-800:]
    tail = close.split("\n\n")[-1] if "\n\n" in close else close
    last = final_sentence(t)

    def ev(rx, s):
        m = rx.search(s)
        return m.group(0).strip()[:70] if m else ""

    asked = bool(OFFER.search(tail)) or "?" in tail
    if not asked:
        return _r("none", True, "")

    # async status note about work already running: not a request
    if ASYNC_NOTE.search(tail) and not MENU.search(tail) and not SURRENDER.search(tail):
        return _r("async-note", IN_FLIGHT.search(t) is not None,
                  ev(ASYNC_NOTE, tail), "in-flight" if IN_FLIGHT.search(t) else "unbacked")

    # A blocker only counts when it is stated IN the ask, not merely somewhere
    # nearby: v2 searched the whole closing and called plain handbacks "blocked"
    # because an unrelated clause mentioned something not being the agent's.
    sents = re.split(r"(?<=[.!?])\s+", close)
    ask_i = next((i for i, sn in enumerate(sents)
                  if OFFER.search(sn) or "?" in sn), None)
    scope = ""
    if ask_i is not None:
        scope = " ".join(sents[max(0, ask_i - 1): ask_i + 2])

    # A genuine blocker outranks the shape the ask is written in. Asking "how do you
    # want to handle this?" about an irreversible SMS to a real person is correct;
    # the phrasing is a style issue, not permission-seeking.
    # A work menu is a violation regardless of any blocker stated elsewhere.
    if WORK_MENU.search(tail):
        return _r("menu", False, ev(WORK_MENU, tail))
    # Strong blockers: the closing, plus the message head where a constraint is
    # often stated before the work is described.
    head_and_close = t[:400] + "\n" + close
    for name, rx in STRONG:
        if rx.search(head_and_close):
            return _r("blocked", True, ev(rx, head_and_close), name)
    for name, rx in WEAK:
        if scope and rx.search(scope):
            return _r("blocked", True, ev(rx, scope), name)

    if CONTINUE.search(tail):
        return _r("continue", False, ev(CONTINUE, tail))
    if MENU.search(tail):
        return _r("menu", False, ev(MENU, tail))
    if SURRENDER.search(tail):
        return _r("surrender", False, ev(SURRENDER, tail))
    if DECISION.search(t) and (
            (len(last) <= 130 and REDIRECT.search(last)) or UNLESS.search(tail)):
        return _r("redirect", True, ev(DECISION, t))
    return _r("handback", False, ev(OFFER, tail) or "question with no decision or blocker")


def _r(cls, ok, why, kind=""):
    return {"close_class": cls, "close_ok": ok, "close_why": why, "close_kind": kind}
