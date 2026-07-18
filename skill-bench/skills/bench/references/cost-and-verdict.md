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
projects above it (realized in `benchmarks/2026-07-17-thirdparty-writing-plans/`); the stop
rule and the mechanical gate must be the same number.

## Scoring

Each cell scores the fraction of its expectations met, after the grade-then-prosecute min rule (see
[judging.md](judging.md)). Fraction-met is arity-generic: the fixed four-expectation decision rubric
and variable-length skill-eval rubrics both work.

## The verdict

Arm means are the mean fraction-met per arm. The headline contrast is clustered by scenario: the
mean of the per-scenario deltas, with a 95% CI over those clusters. The verdict reads the point
estimate for direction (KEEP when the structured arm leads, CUT-CANDIDATE otherwise) and treats the
CI as a confidence signal — strong when it clears zero, weak when it straddles it.

## Reading it honestly

Cluster counts are small (often eight scenarios), so CIs are wide and every verdict is exploratory,
not significance. A weak KEEP with a straddling CI is "no detectable difference," not "it works." A
judge flip between families, or a verdict that only holds under one grader, is a reason to re-measure
rather than to conclude. Report the direction and the caveat together; never launder a wide-CI point
estimate into a claim.

Post-grading, run the arm-asymmetric overturn check (`scripts/lib/overturn.py --dir <dir>
--pattern <regex>`, the regex pre-registered as the decision signature): cells in different arms
carrying the same decision but different verdicts on an expectation are sampled for judge
consistency before any bar they feed is interpreted.
