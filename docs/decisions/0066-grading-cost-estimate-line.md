---
id: 0066
title: "Pre-registrations state a numeric judge/grading-cost estimate"
status: accepted
tier: lite
summary: "Every skill-bench pre-registration carries a numeric judge/grading-cost estimate on the notional basis; a measured figure >2x the estimate is recorded in the verdict README and the routing ADR's Act. One line in cost-and-verdict.md; no gate machinery. Closes #188."
---

# 0066 — pre-registrations state a numeric judge/grading-cost estimate

- Decision: every skill-bench pre-registration states a NUMERIC judge/grading-cost estimate
  on the existing notional basis; when the measured figure exceeds the estimate by more than
  2x, the gap is recorded in the verdict README and the routing ADR's Act. Adopted as one
  line in `skill-bench/skills/bench/references/cost-and-verdict.md`; no script or gate — a
  hard stop on subscription-billed notional spend is machinery without dollars (declined).
- Why: grading spend had no analogous checkpoint to generation's cost-pilot + `cost_gate`,
  and the gap class is twice-observed (ADR 0061's "dual costs <$1" premise measured 17x
  higher; the armd-era grading was never pre-estimated at all). Notional cost is real
  capacity — cost-and-verdict.md's own contract is "$0 marginal, not $0 real".
- Enforced: the cost-and-verdict.md line — the cost-accounting home every /bench
  pre-registration cites — plus the existing pre-reg review step; estimate-vs-actual is
  checkable per run from `notional_cost_usd`.
