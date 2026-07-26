---
id: 0025
title: "Benefit-verdict metric: fraction-met headline, not binary all-or-nothing pass"
status: accepted
tier: lite
summary: "Refines ADR 0024's cost-justification loop: headline metric is fraction-met (continuous, met/total per cell), not binary all-met, since binary floors on hard multi-expectation evals while the eval-clustered CI (ADR 0019) width-warns everywhere. KEEP bar unchanged; the ADR 0019 prosecutor now applies uniformly to every cell's met-count, giving partial credit the same adversarial scrutiny. Binary all-met stays a secondary diagnostic."
---

# 0025 — benefit-verdict metric: fraction-met over binary pass

- Date: 2026-07-09
- Decision: per-cell HEADLINE score is fraction-met (met/total of a cell's expectations, continuous in [0,1]), not binary all-met. The verdict is the eval-clustered mean delta (with - without) + 95% CI (ADR 0019); the KEEP bar is unchanged. The ADR 0019 prosecutor runs UNIFORMLY on every cell's met-count (met_final = min(grader, prosecutor)), not only on binary passes. Binary all-met is retained as a secondary diagnostic.
- Why: on the skills grid (144 cells) binary floored at 21/144 passes — most evals scored 0/0 in both arms, firing a width warning everywhere. Same graded data: binary overall +0.042 (CI straddles 0, CUT-CANDIDATE) vs fraction-met +0.088, 95% CI [+0.019, +0.156] (KEEP). The uniform prosecutor RAISED the delta (+0.075 -> +0.088), so the result survives adversarial scrutiny rather than grader leniency.
- Rejected: keep binary as headline — floors on hard evals, discarding the marginal effect the loop exists to detect. Fraction-met without the uniform prosecutor — partial credit escapes adversarial scrutiny. Require both to clear — reinstates the floor as a veto.
- Reopen-if: a fraction-met win is traced to trivial-expectation inflation -> weight expectations by load-bearingness, or gate on the decisive one.
- Enforced: `aggregate.py` (emits both metrics from the same graded data).
