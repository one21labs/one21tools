# 2026-10-12 G<8 shortfall batch — VERDICTS PROVISIONAL (FRAME-UNCHECKED)

Issue #322 / ADR 0100: the five (skill, model) pairs that stayed below 8 surviving evals in
`../2026-10-12-skill-vs-bare-two-models/` got one more blind-authored round (ids 11+) and a fresh
grid. Pre-registration: `metadata.json`, committed before any generation. Every verdict here was
graded by Claude Opus 5.5, the generators' family, so none may back a README KEEP until a
cross-family judge grades the same committed cells (`grade.py --judges grok`, then
`aggregate.py --judge grok`). No cross-lineage CLI was installed in this container.

## Result (with − without fraction-met; eval-clustered 95% t-interval; 2 reps per cell)

| model | skill | G | bare | with | delta [95% CI] | mde80 | verdict | status |
|---|---|---|---|---|---|---|---|---|
| Sonnet 5.5 | building-skills | 8 | 0.527 | 0.829 | +0.302 [+0.053, +0.552] | 0.344 | KEEP | batch |
| Sonnet 5.5 | code-standards | 8 | 0.529 | 0.896 | +0.367 [+0.104, +0.629] | 0.362 | KEEP | batch |
| Opus 5.5 | code-standards | 6 | 0.494 | 0.892 | +0.397 [+0.109, +0.685] | 0.391 | KEEP | diagnostic (G<8) |
| Opus 5.5 | optimizing-context | 6 | 0.650 | 0.708 | +0.058 [−0.015, +0.132] | 0.099 | INCONCLUSIVE | diagnostic (G<8) |
| Sonnet 5.5 | optimizing-context | 5 | 0.723 | 0.780 | +0.057 [−0.008, +0.121] | 0.087 | INCONCLUSIVE | diagnostic (G<8) |

Arm means are scenario-weighted over matched evals, so with − bare equals the delta. No pair is
HARMFUL. Per-eval deltas, win rates and dropped evals: `results-claude-opus-5-5.json`.

## How to read it

- **ADR 0100's stop rule fires for three pairs.** code-standards on Opus and optimizing-context on
  both models are below G=8 after this round. Their measured claims are recorded as unmeasured;
  the numbers above stay diagnostic. ADR 0100's reopen-if also fired: the new blind tasks
  saturated at or above the 12-Oct rate (Opus 15 of 16, Sonnet 15 of 19 dropped as
  bare >= 0.85), so blind authoring is not converging on these skills. No third round.
- **Two pairs reached G=8, both KEEP**, both FRAME-UNCHECKED (same-family judge).
- **The ADR 0101 confirmatory split fired** (pre-registered secondary, pooled over in-scope
  (model, eval) clusters):

  | eval provenance | clusters | bare | delta [95% CI] |
  |---|---|---|---|
  | original (ids 1-6, written with the skill in view) | 20 | 0.452 | +0.366 [+0.228, +0.503] |
  | blind, 12-Oct (ids 7-10, made the post-hoc lead) | 8 | 0.700 | +0.106 [+0.014, +0.198] |
  | blind, new (ids 11+, confirmatory) | 5 | 0.820 | +0.040 [−0.028, +0.108] |

  The new-blind interval excludes the original point estimate, so the reopen-if pre-registered
  in ADR 0101 fired (ADR 0101 now records the follow-on decision): the KEEPs above rest mostly
  on original evals and are suspect as measures of task value. Two readings
  remain open and this design cannot separate them: expectations written with the skill in view
  reward the skill's own doctrine (#317), or blind tasks are simply easier (bare 0.82 vs 0.45),
  leaving less room to gain. Only 5 new-blind clusters survived the prescreen.

## Exclusions (never scored 0, #191)

11 grid cells, all Sonnet, replied with fake tool-call markup through 3 passes: building-skills
E2 (1 bare rep), E3 and E5 (both bare reps), optimizing-context E2 (both bare reps) and E6 (all
four cells). E3 and E5 drop out of Sonnet building-skills (G 10 -> 8); E2 and E6 out of Sonnet
optimizing-context (G 7 -> 5). E3 is the eval the 12-Oct selection silently dropped
(`unscreened` in `selection.json`); it was kept here and lost to the same markup failure.

## Deviation

One, recorded in `metadata.json` `deviations`: a home path in building-skills E11's prompt was
redacted to satisfy the public-repo path gate, after its prescreen cell was generated; that cell
was regenerated on the edited text before any grid cell existed.

## Costs

Generation $7.28 + Opus judge $5.81 = $13.09 billed, every attempt counted (ERROR cells and
regenerated cells included). Ceiling $54 (the unspent part of the owner's $100 for 12-Oct).

## Reproduce

```bash
python3 prep.py && python3 overlap.py
python3 run_all.py   # prescreen -> grade -> select -> pilot -> cost gate -> grid -> grade -> aggregate
```
