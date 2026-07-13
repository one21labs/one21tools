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
