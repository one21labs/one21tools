# Retune re-benchmark — FAILED, reverted (2026-07-07)

Hypothesis: rewriting the 5 ceiling/dead evals harder would make them discriminate at opus and
lift the skill×model cells that fall below ADR 0019's 4-non-tied-eval floor. Re-benchmarked the
5 rewritten evals × 3 models × 2 configs × 3 runs (90 runs, 30 graded cells, unblinded — same
contract as the grid, so before/after is comparable). Result: the hypothesis did NOT hold.

## Per-eval mean delta (with − without), before (v2 grid) → after (retune)

| Skill / model / eval | before | after | outcome |
|---|---|---|---|
| code-standards haiku e2 | +0.110 | −0.057 | REGRESSED to negative |
| code-standards haiku e3 | +0.003 | +0.057 | small improvement |
| code-standards sonnet e2 | 0.000 | +0.053 | now discriminates (positive) |
| code-standards sonnet e3 | 0.000 | −0.110 | now discriminates NEGATIVE |
| code-standards opus e2 | 0.000 | −0.057 | now NEGATIVE |
| code-standards opus e3 | +0.057 | +0.113 | improvement |
| engineering-principles haiku e3 | +0.053 | −0.273 | badly REGRESSED |
| engineering-principles sonnet e3 | +0.003 | +0.053 | small improvement |
| engineering-principles opus e3 | 0.000 | −0.057 | now NEGATIVE |
| optimizing-context haiku e3 | 0.000 | 0.000 | still dead |
| optimizing-context haiku e4 | +0.333 | +0.160 | weaker (still positive) |
| optimizing-context sonnet e3 | 0.000 | +0.170 | FIXED (only clean win) |
| optimizing-context sonnet e4 | 0.000 | −0.053 | now slightly NEGATIVE |
| optimizing-context opus e3 | 0.000 | 0.000 | still dead |
| optimizing-context opus e4 | +0.067 | +0.057 | ~unchanged tie |

**Tally:** 6 cells went negative, 2 stayed dead, several got weaker; exactly 1 clean fix
(oc-e3/sonnet). Net: the retune introduced more spurious negatives than discrimination.

## Why it failed (analysis)

- **"Harder" ≠ "discriminates for the skill."** Several rewrites made the task harder in ways
  where the with-skill arm scored WORSE than baseline — either the skill's guidance misleads on
  the harder task (same failure class as the engineering-principles haiku loopholes, #27, which
  is NOT on this branch), or the fresh-authored assertions penalize skill-following, or both.
- **n=3 is noisy** for small deltas; the ±0.05 cells are within noise, but ep/haiku −0.273 and
  the two still-dead oc cells are not noise-explained.
- **A negative-delta eval is worse than a ceiling.** A ceiling adds a harmless tie; a spurious
  negative drags the skill's verdict down. Shipping these would DEGRADE the eval sets' validity.

## Decision: revert

The retuned evals are NOT validated, so they were reverted from `toolkit-evals-v2` (#25),
restoring the v2 sets. The v2 ceilings on some strong-model cells are a known, documented
limitation (grid results.md); they are the validated baseline. The retune commit remains in git
history and this record for anyone iterating.

## If iterating (future work)
- Retune ONE eval at a time and re-benchmark before the next — batch rewrites hid which changes
  helped vs hurt.
- Have the eval author's assertions written by a SEPARATE fresh instance (author-separation) and
  check each assertion DISCRIMINATES on a 1-run probe before committing to 3× replicates.
- For a persistent negative, first check whether the skill genuinely hurts at that tier (a real
  finding) vs the assertions being mis-aimed — grade the failing outputs by hand.
- Re-test engineering-principles evals only AFTER #27 (the loophole fix) is on the branch.
