# 2026-10-12 skill vs bare, Claude Opus 5.5 and Claude Sonnet 5.5 — VERDICTS PROVISIONAL (FRAME-UNCHECKED)

Owner directive 12-Oct: test each measured skill against the bare model on Opus 5.5 and on
Sonnet 5.5. Pre-registration: `metadata.json` (committed before any generation). Also ADR 0095's
first batched re-measure. Every verdict below was graded by Claude Opus 5.5 — the generators'
family — so none may back a README claim until a cross-family judge grades the same committed
cells (`python3 grade.py --dirs outputs --judges grok`, then `aggregate.py --judge grok`).

## Result (with − without fraction-met; eval-clustered 95% t-interval; 2 reps per cell)

| model | skill | G | bare | with | delta [95% CI] | mde80 | verdict | status |
|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | building-skills | 10 | 0.618 | 0.942 | +0.323 [+0.107, +0.540] | 0.301 | KEEP | batch |
| Opus 5.5 | engineering-principles | 8 | 0.635 | 0.777 | +0.142 [−0.091, +0.375] | 0.321 | INCONCLUSIVE | batch |
| Opus 5.5 | code-standards | 6 | 0.458 | 0.844 | +0.386 [+0.092, +0.680] | 0.399 | KEEP | diagnostic (G<8) |
| Opus 5.5 | optimizing-context | 5 | 0.670 | 0.673 | +0.003 [−0.077, +0.084] | 0.108 | INCONCLUSIVE | diagnostic (G<8) |
| Sonnet 5.5 | engineering-principles | 9 | 0.613 | 0.702 | +0.089 [−0.070, +0.248] | 0.220 | INCONCLUSIVE | batch |
| Sonnet 5.5 | building-skills | 7 | 0.548 | 0.875 | +0.309 [−0.001, +0.620] | 0.425 | INCONCLUSIVE | diagnostic (G<8) |
| Sonnet 5.5 | code-standards | 7 | 0.545 | 0.910 | +0.364 [+0.094, +0.635] | 0.370 | KEEP | diagnostic (G<8) |
| Sonnet 5.5 | optimizing-context | 5 | 0.548 | 0.677 | +0.103 [−0.048, +0.254] | 0.202 | INCONCLUSIVE | diagnostic (G<8) |

Per-eval deltas and win rates: `results.json`. No (skill, model) pair is HARMFUL.

## How to read it

- **One batch-grade KEEP**: building-skills on Opus 5.5. code-standards clears zero on BOTH models
  but at G=6-7, so it is diagnostic only (ADR 0095 decision 4): it may support a claim's
  direction, never discharge the debt for a KEEP.
- **engineering-principles is INCONCLUSIVE on both models at G>=8**: its interval runs from a
  small harm to a large gain; the design could only reliably detect +0.22..+0.32.
- **optimizing-context shows nothing on Opus 5.5** (+0.003, tight interval, mde80 0.108) — the
  closest thing here to a measured null, still only G=5.
- **Multiplicity**: 8 intervals at 95% expect ~0.4 false calls under a global null; the three
  KEEPs are 0.09-0.11 clear of zero, not marginal, but read them with that in mind.
- **Not comparable to the July baselines**: three isolation defects were fixed for this run
  (metadata.json `isolation_changes_vs_2026-07`, `aborted_runs`), so no trend is read across.

## Exclusions (never scored 0, #191)

- 2 grid cells: both bare Sonnet reps of building-skills E5 replied with fake tool-call markup
  through 3 passes, so E5 drops out of Sonnet building-skills (G 8 -> 7, batch -> diagnostic).
- 2 prescreen cells, same failure (Sonnet), excluded from selection.
- The markup filter is a SELECTION: it removes replies where the model acted out an agent loop.
  It fired on both arms (16 distinct grid cells flagged at least once, 10 of them with-arm),
  Sonnet only; all but the 2 above came back clean on a regeneration pass.

## Selection

Prescreen (1 bare rep per eval per model): bare >= 0.85 dropped for that model — 11 of 40 on
Opus, 10 on Sonnet (`selection.json`). The blind-authored evals (E7-E10) saturated more often than
the originals; overlap with each skill's own wording: `overlap.json`.

## Costs

Generation $30.39 + Opus judge $13.77 billed (~$1.5 more unrecorded from a grading pass
interrupted mid-run) ≈ $45.7 of the owner's $100 cap. Of that, $18.25 went to the two aborted
runs (`aborted-*`, kept for the record, never graded into these results).

## Reproduce

```bash
python3 prep.py && python3 overlap.py
python3 run_all.py   # prescreen -> grade -> select -> pilot -> cost gate -> grid -> grade -> aggregate
```
