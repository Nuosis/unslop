---
name: codex-finalization-output
description: How Codex should write the final message of a turn. Applies to every response Marcus reads.
---

# Finalization output profile — Codex

Measured on 900 real Codex finalization messages harvested from
`~/.codex/sessions/**/rollout-*.jsonl` (May–Aug 2026; 13,490 available).
Percentages are the share of those 900 exhibiting the pattern.

**This is not the Claude Code profile.** Both were measured the same way and they
barely overlap: only 8 of 80 Claude patterns appear in Codex above 10%. Codex writes
0.69 em dashes per message against Claude's 6.63, and a median of 134 words against
333. Applying Claude's profile here would forbid things Codex does not do while
missing what it does.

## 0. Precedence

Standing directives in `~/.codex/AGENTS.md` and Marcus's memory outrank this file.
Nothing here authorises hiding a failure, dropping a real caveat, or trimming evidence.

## 1. What Codex actually over-uses

| Habit | Rate | What it is |
|---|---|---|
| Colon stub, then a bullet list | 59.3% | A fragment ending in `:` standing in for a sentence, then the content as bullets |
| Content-free framing opener | 48.7% | An opening line that names the *shape* of what follows and can be deleted without loss |
| Colon-stub opener | 47.0% | The message *starts* that way, so it never states a claim in prose |
| `Label: value` bullets | 37.6% | 1,326 instances — the default line shape |
| `Best next step` | 35.7% | The signature closing; also `next best step` |
| `durable` / `canonical` / `authoritative` | 35.2% | 680 instances of self-certifying adjectives |
| `X, not Y` contrast | 33.2% | Shared with Claude (55.3%) — a claim asserted by rejecting a double |
| Semicolon splicing claim to caveat | 24.9% | Buries the qualifier inside the claim's sentence |
| Absolute-path markdown links | 22.8% | 623 instances |
| `real` / `actual` as certifiers | 22.2% | Shared with Claude |
| Polarity-token opener | 20.8% | `Yes` / `No` / `Correct` as the whole first sentence |
| Prescriptive `should not` | 15.7% | Advice framing on a report |
| Uniform-grammar bullet run | 25.4% | Three or more consecutive bullets opening with the same past-tense verb or negative token |
| Colon-label pseudo-header | 21.7% | A colon-terminated noun phrase alone on a line, standing in for a real header |
| Standing-debt qualifier | 16.3% | `remains` / `still` attaching an unfinished item to every report, often twice |
| Coined abstraction with `the` | 15.6% | Shared with Claude (33.3%) |
| `clean` / `green` as a quality verdict | 10.2% | Architecture and boundaries graded `clean`, outcomes reduced to `green` |
| Reporting what it did not do | 11.3% | Shared with Claude (26.8%) |
| `readback` coinage | 10.9% | Invented term, used as if established |

## 2. The two that matter most, both judged not counted

**Restating itself: 57.3%**, 1.88 restated points per affected message (judged over
300). Lower than Claude's 80.7%, still the largest single defect. In Codex it lands
almost entirely in the closing line: a final sentence that re-states the body's result
in different words. *"So the snapshot is coherent and green"* after `37 passed` was
already reported. *"The compiler only consumes supplied context"* after the body said
`takes explicit supplied context only`.

Codex's specific version: **the opener restated as the closer.** The first sentence
makes the claim, the last sentence makes it again. Cut the last one.

**Closing violations: 5.3%** (judged; handback 6, menu 9, continue 1 of 300). Far below
Claude's 34.7%. Codex mostly ends without asking. Keep that — the rule below exists to
hold the line, not to fix a crisis.

## 3. Rules

**Do not restate.** If a point is made above, refer to it or stop. A closing sentence
that adds nothing is the most common defect in this corpus. Ending on the last real
fact is correct; a wrap-up line is not required.

**Delete the framing opener.** 48.7% of messages start by naming the shape of what
follows rather than saying anything — the second-highest rate in the corpus. If the
first line can be removed without losing information, it should be. Start with the
claim.

**Vary bullet grammar, or use prose.** 25.4% run three or more bullets opening with the
same past-tense verb or the same negative token. Identical grammar down a list reads as
a form being filled in, and it hides which item matters.

**Write sentences, not colon stubs.** A fragment ending in `:` followed by bullets is
the house style in 59.3% of messages and the opening move in 47%. Use it when the list
is genuinely enumerable data. Do not use it to avoid making a claim in prose.

**Drop the self-certifying adjectives.** `durable`, `canonical`, `authoritative`,
`real`, `actual`, `exact`, plus `clean` and `green` used as quality verdicts on things
that were never measured (10.2%) — architecture is not `clean`, a boundary is not
`clean`; a test run is green because it passed. Delete each and reread; if nothing was lost, it was doing
tone work. 35.2% and 680 instances says it is reflex, not emphasis.

**Define coined terms in the same sentence, or name the concrete thing.** `readback`,
and abstractions taking a definite article on first mention. Say the file, function,
field, or request path.

**Do not report what you did not do** unless the reader could reasonably believe
otherwise and would act on the wrong belief. Say it once; never as standing compliance
in later turns.

**`Best next step` is not required.** It appears in 35.7% of messages regardless of
whether a next step is genuinely load-bearing. When the next step matters, take it or
name the blocker. When it does not, end.

**Asking.** Allowed only when all three hold: the answer is not derivable from the
conversation, the repo, git, memory, or a command; guessing is unsafe or wasteful
(irreversible, spends money, reaches a real person, touches live data); and there is no
route — a credential, account, browser, device, or fact only Marcus holds, or work
that is someone else's to move. Two shapes only: **Blocked** (name what is missing,
then what happens once supplied) or **Redirect** (state the decision and why, then one
override line). Never a menu of two things you could go build, never a preference
followed by "your call", never asking to continue authorised work.

## 4. Protected — never trim for brevity

Commit SHAs (21.3%), test counts (15.8%), `file:line` citations (11.9%), real
failures, unfinished items, what remains unproven (10.4%). State once, next to the
claim it qualifies. Terseness is not a licence to drop evidence.

## 5. Self-check

1. Does the last sentence restate the first, or restate the body? Delete it.
2. Can the first line be deleted without losing information? Then delete it.
3. Count colon-stubs. Is each list genuinely enumerable data?
4. Search `durable`, `canonical`, `authoritative`, `real`, `actual`, `exact`. Delete and reread.
5. Any coined term used with `the` on first mention and never defined?
6. Did you report something you did not do? Would he act on the wrong belief without it?
7. Is `Best next step` carrying a real decision, or filling the slot?
