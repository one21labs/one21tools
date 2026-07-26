---
id: 0036
title: "routing-escalation verdict: do not adopt; model-judge false-accept replicates, checklist checkers solve fidelity but not cost"
status: accepted
tier: lite
summary: "Issue #109 measured: routing (haiku attempts once, a checker ships or escalates, sonnet redoes whole) fails the cost gate for every checker variant (1.04-1.33x sonnet-solo vs <=0.6x target) because a faithful checker escalates ~3/4 of cells. Model-judge false-accept replicates #41; a checklist checker solves fidelity but not cost. ADR 0035's tier-by-work-type doctrine stands."
---

# 0036 — routing-escalation verdict

- Decision: do not adopt routing. Every checker variant failed the pre-registered cost gate
  (median <=0.6x sonnet-solo): sonnet-judge 1.68x, haiku-judge 1.42x, mechanized 1.24x — only
  6/24 haiku cells on this battery are legitimately shippable, so a faithful checker escalates
  ~3/4 of cells and routing pays haiku + checker + sonnet on most of them. ADR 0035's
  tier-by-work-type doctrine gains a second leg: no cascade shape rescues attempt-first-cheap on
  judgment-heavy work.
- Why: #41's 25% validator false-accept REPLICATES for model judges under routing (sonnet-judge
  21%, haiku-judge 25%); a deterministic checklist checker solves fidelity (8%, quality delta
  -0.010) but still costs more than sonnet-solo where the cheap model rarely suffices.
- Rejected: adopt mechanized-checker routing for quality (costs MORE than sonnet-solo; the issue's
  premise was cost reduction) — a live routing arm (composition is exact; adds spend, not
  information) — tune the checker threshold post-hoc (moving the bar after unblinding, ADR 0024
  forbids it).
- Reopen-if: a production-shaped task mix shows escalation rate <=~0.3 under a <=15% false-accept
  checker -> re-test.
- Enforced: `benchmarks/2026-07-10-routing-escalation/metadata.json`, `results.jsonl`.
