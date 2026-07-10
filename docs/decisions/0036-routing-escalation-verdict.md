---
id: 0036
title: "routing-escalation verdict: do not adopt; model-judge false-accept replicates, checklist checkers solve fidelity but not cost"
status: accepted
summary: "Issue #109 measured (benchmarks/2026-07-10-routing-escalation, pre-registered bar): routing (haiku attempts once, a checker ships or escalates, sonnet redoes escalated tasks whole) fails the cost gate for every checker variant — 1.04–1.33x sonnet-solo total cost against <=0.6x — because a faithful checker escalates ~3/4 of cells on this battery. #41's validator false-accept replicates for model judges (sonnet 21%, haiku 25%); a deterministic checklist checker solves fidelity (8% false-accept, quality -0.010 vs sonnet-solo) but cannot make routing cheap where the cheap model rarely suffices. ADR 0035's tier-by-work-type doctrine stands."
---

# 0036 — routing-escalation verdict

- Date: 2026-07-10
- Owner: PM (verdict read mechanically off the pre-registered bar)
- Panel: none — the bar, checker variants, and false-accept ground truth were pre-registered in
  metadata.json and committed before any checker call; the verdict is arithmetic.
- Context: issue #109 proposed the cascade-literature routing shape left untested by #41's
  rejected tiered config: haiku attempts the task once, a checker decides ship-or-escalate, and an
  escalated task is redone WHOLE by sonnet (no coaching), so quality is bounded by whichever model
  ships rather than by haiku's ability to incorporate feedback. The #41 fullgrid's blind-graded
  haiku-solo and sonnet-solo gradient cells (8 evals x 3 reps, real per-cell envelope costs) are
  the two halves of the routing arm, so the run composed them offline — the only new spend was 48
  hermetic checker calls (ADR 0023 executor) plus a $0 offline variant. Checker variants:
  sonnet-judge and haiku-judge (request + deliverable only, no rubric), and mechanized (ship iff
  all of the eval's deterministic structural checks pass; rubric-informed, an upper bound for
  hand-written task-type lint checks).

## Decision
1. **Do not adopt routing.** Every variant failed the pre-registered cost gate (median per-cell
   cost <= 0.6x sonnet-solo): sonnet-judge 1.68x, haiku-judge 1.42x, mechanized 1.24x (totals
   1.04–1.33x). The failure is structural, not a checker defect: only 6/24 haiku cells on this
   battery are legitimately shippable, so a faithful checker escalates ~0.75–0.79 of cells and
   routing pays haiku + checker + sonnet on most of them. Where the cheap model rarely suffices,
   no checker can make routing cheap.
2. **Record the checker-fidelity finding — the experiment's pre-registered primary secondary
   metric.** #41's 25% validator false-accept REPLICATES for model judges under routing semantics
   (sonnet-judge 5/24 = 21%, haiku-judge 6/24 = 25%). The deterministic checklist checker solves
   it: 2/24 = 8% false-accept, quality delta -0.010 vs sonnet-solo (CI [-0.047, +0.027]; lower
   bound clears the -0.05 margin even at n=8). Model self-report of "is this good enough" is the
   weak link; mechanized checks are the reliable form of acceptance testing on structure-bound
   work.
3. **ADR 0035's doctrine stands and gains a second leg:** tier by work type, not by task-level
   routing. Even the optimal cascade shape (no coaching, whole-task redo, near-perfect checker)
   cannot rescue a haiku attempt-first policy on judgment-heavy work. No pdca-workflow change.
4. Close #109 with the null recorded append-only (ADR 0024): benchmarks/2026-07-10-routing-escalation/
   (pre-registration commit e631bcc precedes every checker record; results.jsonl is the numbers'
   one home).

## Justification
The bar was committed before any checker call; every number is from committed artifacts
(results.jsonl, checkers/, the #41 fullgrid's graded verdicts and per-cell envelopes). ADR 0024:
adopt only what measurably earns its cost — routing does not, on the only battery measured.

## Assumptions
- [checkable] the verdict reproduces from committed artifacts — owner: gate; result: verified
  2026-07-10 (compose.py re-run reproduces results.jsonl verbatim from checkers/ + the fullgrid's
  graded/ and outputs/cells/; compose_test.py 17/17).
- [unverifiable] routing could pay on a task mix with a high haiku-parity fraction — this battery
  was selected for tasks where haiku loses (pre-registered limitation), the pessimal population
  for routing cost. REOPEN-IF a production-shaped task mix shows escalation rate <= ~0.3 under a
  <=15% false-accept checker; with the mechanized checker's fidelity, routing there would clear
  the cost gate arithmetically.
- [unverifiable] the mechanized checker's 8% false-accept generalizes only to work with
  authorable structural checks — it was rubric-informed here; judgment-heavy acceptance without a
  writable checklist remains the sonnet-judge case (21%).

## Rejected alternatives
- Adopt mechanized-checker routing for quality (delta -0.010, the best non-sonnet config measured
  in either experiment) — it costs MORE than sonnet-solo here (1.24x median); the issue's premise
  was cost reduction.
- Re-run with a live (non-composed) routing arm — composition is exact for this design (no
  coaching, whole-task redo, halves independent); a live run would add spend, not information.
- Tune the checker threshold post-hoc to trade fidelity for escalation rate — moving the bar
  after unblinding is the failure ADR 0024 D3 forbids; recorded as a revisit trigger instead.

## Revisit triggers
- A production-shaped task mix (high haiku-parity fraction) becomes measurable -> re-test routing
  there; the mechanized checker's fidelity makes the cost arithmetic the only open question.
- Haiku-tier capability or pricing shifts materially -> the 6/24 shippable floor moves; re-check.
- A workload with authorable acceptance checks needs cost reduction -> reuse the mechanized-checker
  pattern (benchmarks/lib/mechanized_checks.py) as the acceptance gate regardless of routing.
