---
name: unslop
description: Use this skill when you need to run the unslop repo, analyze a domain for repetitive AI defaults, generate a reusable skill file, and verify that the output is specific and materially different from the baseline.
---

# unslop

Use this repo to generate a domain-specific profile that removes repetitive AI defaults.

## Workflow

1. Clone `https://github.com/mshumer/unslop` if the repo is not already present.
2. Enter the repo root and use a Python virtual environment.
3. Decide whether the job is `text` or `visual`.
   Text: writing, emails, essays, tutorials, copy, code explanations.
   Visual: websites, landing pages, HTML pages, UI mockups.
4. Install Playwright only for visual runs:
   `pip install playwright && playwright install chromium`
5. Decide whether the domain has a PRINCIPAL — a specific person who reads this
   output and has already said how they want it. If yes, you must pass their
   standing directives, or the profile will read as if their preferences were
   defects. See "Domains with a principal" below.
6. Run the tool:
   `python3 unslop.py --domain "<domain>"`
   `python3 unslop.py --domain "<domain>" --type visual --count 20 --concurrency 3`
   `python3 unslop.py --domain "<domain>" --directives ~/.claude/CLAUDE.md --directives <memory-dir>`

## Domains with a principal

unslop is subtractive by default: it names defaults to stop using and refuses to
prescribe alternatives. That is right for generic prose. It is wrong when a named
person reads the output, because "prescribe no alternatives" becomes "encode none
of their preferences" — the profile then treats every recurring shape as a defect,
including the ones that person explicitly demanded.

- `--directives <path>` — a file or directory of instructions the reader has already
  given. Repeatable. The skill file then splits every pattern three ways: VIOLATES a
  directive (hard rule, reported as a compliance rate), REQUIRED by a directive
  (protected — placement and length rules only, never removal), or FREE-FORM (normal
  subtractive treatment).
- `--preferences <path>` — a file stating how they want output to look. Encoded as
  positive requirements. This is the one place the tool is allowed to prescribe.

Without `--preferences`, the run does not end at `skill.md`. It adds a final step that
rewrites real samples under the new profile and writes `preference-request.md` — the
original and the rewrite side by side, then a direct request for the target. A profile
derived only from what to avoid is unvalidated until the reader has seen output and
said whether it matches what they wanted.

**Do not skip this by guessing the preference.** If you find yourself inventing a rule
to patch a gap the tool left, that gap is the thing to ask about.

## Output Review

Check `unslop-output/analysis.md` and `unslop-output/skill.md`.

- `analysis.md` must be concrete, counted, and specific. Prefer exact counts over a
  model's estimate: compile each pattern to a regex and re-count across the whole
  sample set, rather than trusting per-shard frequencies.
- `skill.md` should mostly say what to avoid, not prescribe one new stock style — but
  where `--directives` were supplied, check it did not tell the reader to stop doing
  something those directives require. That is the failure mode to look for first.
- `preference-request.md` (when present) must hold the information constant between
  original and rewrite. If a rewrite dropped a number, an identifier, or a caveat, it
  is wrong regardless of how much shorter it got.
- For visual runs, compare `unslop-output/before-after/before.html` and `unslop-output/before-after/after.html`.
- The `after` result should feel meaningfully less generic than `before`.

If the analysis is thin or obviously missed repeated patterns, rerun or rewrite the analysis from inside `unslop-output` after reviewing the screenshots and sample files directly.

## Deliverable

Return:

- The generated `skill.md`
- The main repeated patterns the analysis found
- A worked before/after example on real samples — not a description of what would
  change. The reader cannot judge a writing profile they have not seen applied.
- Any caveats about sample quality, missing screenshots, or weak comparison output
- If no `--preferences` were supplied: the open question from `preference-request.md`,
  stated as an open question. The run is not finished until it is answered.
