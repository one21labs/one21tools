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

There is deliberately no verdict meaning "probably a bit better", because no such claim is
supportable from a straddling interval.

**The practical bar is pre-registered or it is worthless.** It is the smallest difference worth
paying context for. Testing it against the LOWER bound is what turns "better than nothing" into
"clearly better". Choosing it after seeing which way the numbers went is the exact failure
pre-registration exists to prevent. Left at 0, the bar is bare significance — the weakest
defensible setting, not the recommended one.

**CUT needs the bar.** With no bar, a null result is INCONCLUSIVE forever: you cannot prove a
difference is smaller than nothing. The rule shipped until 2026-07-27 reached CUT-CANDIDATE from a
point estimate near zero, which is indistinguishable from an underpowered run — that is how a
null could be laundered into a decision.

Every verdict carries **`half_width`** and **`mde80`** (below), plus **`win_rate`**, the share of
scenarios the treatment actually won. A mean carried by one scenario is not "clearly better most
of the time"; the interval alone cannot tell you which you have, so the win rate is reported
beside it. It has no inferential status — over 6-8 scenarios it is a coin-flip count with no
interval, so read it as a prompt to check attribution, never as a criterion.

## Reading it honestly

Cluster counts are small, so intervals are wide. **Read `mde80` before reading the mean.** An
INCONCLUSIVE verdict whose observed mean is below `mde80` means the run was underpowered for the
effect it saw — not that the effect is absent. Those are opposite conclusions, and the point
estimate cannot tell them apart.

`half_width` and `mde80` are both reported and are not the same number. A true difference equal to
the half-width clears zero only about **half** the time, so half-width is a 50%-power figure;
treating it as "what the design can detect" overstates the design by about 40%. `mde80` is what it
calls reliably. Sizing the NEXT run from these is design-time work and lives in
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
