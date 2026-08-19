# Claude Code vs Codex — same method, different defects

Both corpora harvested with `harvest.py`, patterns compiled to regex and counted
exactly, non-matchable defects judged by LLM over a stratified sample.

| | Claude Code | Codex |
|---|---|---|
| corpus | 803 messages | 900 (of 13,490 available) |
| median words | 333 | 134 |
| em dashes / message | 6.63 | 0.69 |
| bold spans / message | 6.90 | 1.45 |
| **restates itself** (judged) | **80.7%** | **57.3%** |
| restated points per affected msg | 2.09 | 1.88 |
| closing violations | 34.7% | 5.3% |
| reports what it did not do | 26.8% | 11.3% |
| undefined coined term | 33.3% | 15.6% |
| `X, not Y` contrast | 55.3% | 33.2% |

**Only 8 of 80 Claude patterns appear in Codex above 10%.** The profile does not
port. Applying Claude's rules to Codex would forbid behaviour it does not exhibit —
`**Bold** —` paragraph leads at 69.9% vs 8.6%, pre-announced counts at 39.5% vs 2.4%,
`That's the …` verdicts at 46.9% vs 3.7% — while saying nothing about what Codex
actually over-uses: colon stubs standing in for sentences (59.3%), `Best next step`
as a reflex closer (35.7%), `durable`/`canonical`/`authoritative` as self-certification
(35.2%).

## What is shared

Three defects survive the harness change, which makes them properties of the task
rather than of the model:

1. **Restating itself.** Highest-rate defect in both. Different shape: Claude recaps
   the body in a summary block; Codex repeats the opener as the closer.
2. **Undefined coined terms.** Claude coins architectural abstractions (`the seam`,
   `the spine`); Codex coins process nouns (`readback`). Both use them with a definite
   article on first mention and never define them.
3. **Reporting what it did not do.** Half the rate in Codex, same failure.

Only one pattern is materially stronger in Codex: a one-word polarity verdict plus an
em dash (`Yes —`), 7.2% → 19.9%.

## Method note

The counted pass alone would have missed the top defect in both corpora. No regex
finds distributed prose restatement: the labelled-recap shape is 1.1% of the Claude
corpus against a judged 80.7%, and opener/closer overlap is 4.2% of the Codex corpus
against a judged 57.3%. A count-only run reports both corpora as clean of their worst
problem.
