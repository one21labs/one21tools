---
id: 0042
title: "Paid experiments inherit verdict methodology and pre-spend discipline"
status: accepted
tier: lite
summary: "Three pre-run discipline rules (extend ADR 0024/0025) house in a new sibling reference pre-registration.md: a pre-reg cites the settled verdict methodology instead of restating a superseded metric; a cost-pilot (2-3 cells of the priciest arm) runs before any grid, stopping if a pre-registered gate is already decidable; a size-gated prior-art pass precedes designing a paid experiment."
---

# 0042 — paid experiments inherit verdict methodology and pre-spend discipline

- Decision: house three rules in a new sibling reference `pre-registration.md`
  (empirical-evals.md's near-full headroom takes only a pointer, ADR 0031 split-don't-cram):
  (1) a pre-registration cites empirical-evals.md's verdict methodology instead of restating a
  superseded metric; (2) a cost-pilot (2-3 cells of the most expensive arm) runs before any
  grid, unconditional, stopping if a pre-registered gate is already decidable; (3) a size-gated
  prior-art pass (is the answer already known, in what regime?) precedes designing a paid
  experiment.
- Why: a pre-reg naming a metric the ADRs already superseded caused a recurring binary-floor
  fishing accusation (#107); a decidable cost gate ran ~90% past its stopping point before
  (#105, ~$0.60 vs the full grid). Both ship with building-skills at the same surface
  (pre-run design), so one new home + one pointer.
- Rejected: do nothing beyond ADR 0025 — the floor recurred a third time. Mandate prior-art on
  every experiment — gold-plate on trivial pilots. Cram the three rules into
  empirical-evals.md's headroom — cap breach.
- Reopen-if: a pre-reg again names a superseded metric -> template the comment itself. A grid
  runs past a decidable cost gate again -> cost-pilot needs a hard stop (a gate script).
- Enforced: `pre-registration.md`, alongside `empirical-evals.md` (PR #128).
