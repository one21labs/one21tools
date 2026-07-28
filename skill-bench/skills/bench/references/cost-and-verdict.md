# Cost and verdict

## Notional (shadow) cost

Under a grok.com or Claude Max subscription, a benchmark run adds no per-call charge — it is
marginally free. But it still consumes real usage (quota, rate limits, underlying compute), so the
report prices every run at published per-token API rates from the token counts the CLI reports. This
is pure arithmetic — a fixed rate table times token counts, no model and no network — so it is
deterministic and unit-tested. The figure lets spend be understood regardless of billing mode; it is
$0 marginal, not $0 real.

`notional_cost_usd` in the report carries the judge call count and the priced total. Cached
re-analysis reports zero (no live calls).

A pre-registration states a NUMERIC judge/grading-cost estimate on this same notional basis
(generation spend already has cost-pilot-first + cost_gate; grading had no analogous
checkpoint, ADR 0066). When the measured figure exceeds the estimate by more than 2x, record
the gap in the verdict README and the routing ADR's Act.

**The initial estimate is DERIVED, never guessed (ADR 0076):** take the most recent measured
$/cell for the same judge/model from a prior committed `metadata.json` cost block (grep
`benchmarks/*/metadata.json` for `actuals`); no prior exists → run the 2-cell pilot BEFORE
recording any number. Three guessed estimates missed by 2-17x (ADR 0061; PR #219; PR #227).

**`ceiling_usd` derivation (ADR 0073):** the generation cost gate's `ceiling_usd` is set to 2x
the pre-registered notional estimate — the >2x stop-rule of record — NEVER the estimate itself.
Encoding the estimate band's top as the ceiling forces a mid-run revision the moment a pilot
projects above it (realized in
`one21labs/one21tools:benchmarks/2026-07-17-thirdparty-writing-plans/`); the stop rule and the
mechanical gate must be the same number.

## Scoring

Each cell scores the fraction of its expectations met, after the grade-then-prosecute min rule (see
[judging.md](judging.md)). Fraction-met is arity-generic: the fixed four-expectation decision rubric
and variable-length skill-eval rubrics both work.

## The verdict

Arm means are the mean fraction-met per arm. The headline contrast is clustered by scenario: the
mean of the per-scenario deltas, with a 95% CI over those clusters. **The interval decides the
verdict; the point estimate never does.**

| Verdict | Condition | What you may claim |
|---|---|---|
| KEEP | CI lower bound > the pre-registered practical bar | at least that much better, with 95% confidence |
| HARMFUL | CI upper bound < 0 | measurably worse |
| CUT | the whole CI sits inside +/- the practical bar | no difference worth having — an equivalence result |
| INCONCLUSIVE | anything else | nothing; the run cannot answer |

The table is reproduced here ON PURPOSE and is the one exception to cite-don't-restate in this
file: it is the contract you read a result against, and an adopter should not have to open plugin
source to learn what a verdict word means. Everything ABOUT it — why there is no "probably a bit
better", why the bar is worthless unless pre-registered, why CUT is unreachable without one, and
what `win_rate` may and may not be used for — has one home, `benchstats.keep_verdict`'s docstring.
Read that before setting a bar.

Every verdict also carries `half_width`, `mde80` (below) and `win_rate`, the share of scenarios
the treatment actually won.

## Reading it honestly

Cluster counts are small, so intervals are wide. **Read `mde80` before reading the mean.** An
INCONCLUSIVE verdict whose observed mean is below `mde80` means the run was underpowered for the
effect it saw — not that the effect is absent. Those are opposite conclusions, and the point
estimate cannot tell them apart.

Both are reported and they are not interchangeable: `half_width` is a 50%-power figure and
overstates the design by about 40%, `mde80` is what it calls reliably. Why, in full:
`benchstats.keep_verdict`'s docstring. Sizing the NEXT run from these is design-time work —
[pre-registration.md](pre-registration.md).

A judge flip between families, or a verdict that holds under one grader only, is a reason to
re-measure rather than to conclude.

**Mechanism claims cite cells (#191).** Any causal "the mechanism is X" sentence in a verdict
README cites its supporting cells or carries an exploratory label. A bar miss that flips or halves
without its top contributing cells (`benchstats.top_cell_attribution`) triggers inspection of those
cells for infrastructure failure before interpretation.

Post-grading, run the arm-asymmetric overturn check (`scripts/lib/overturn.py --dir <dir>
--pattern <regex>`, the regex pre-registered as the decision signature): cells in different arms
carrying the same decision but different verdicts on an expectation are sampled for judge
consistency before any bar they feed is interpreted.
