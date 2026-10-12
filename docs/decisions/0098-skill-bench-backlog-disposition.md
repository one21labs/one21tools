---
id: 0098
title: "skill-bench backlog: no new home, honesty first, unclaim rather than wire"
status: accepted
tier: lite
summary: "Issue #310 keeps ownership of the subsystem backlog; ADR 0095's trigger keeps the keep_verdict floor. Order: honesty, then unclaim the prosecutor overstatement rather than paying 2x judge calls forever, then the rename. prereg_guard struck as a non-defect; the contamination sweep kept and a #317 leakage audit added alongside."
---

# 0098 — skill-bench backlog disposition

- Decision: no new backlog home — #310 (38 findings, round 2 of <=6 owed) owns the subsystem;
  ADR 0095's trigger owns the keep_verdict floor. Order: (1) honesty (ADR 0096); (2) scope
  grade-then-prosecute to the verdict path — UNCLAIM, do not wire; (3) rename (ADR 0097);
  (4) the stats menu (AC1/phi, McNemar, permuted expectation order, negative-control fixture,
  look-caps, UCB pilot SD) folds into #310 round 2, none promoted alone. prereg_guard: STRUCK,
  non-defect — tested, and invoked as step 1 of evaluating-your-own-work.md's procedure; an
  agent-run CLI is the wiring for a skill. Contamination: KEEP the history sweep, ADD a #317
  expectation-leakage audit — different defect classes.
- Why: subtract-first — every item closes by deleting a claim or a backlog entry; only the
  leakage audit adds, and it is the one finding no deletion closes.
- Rejected: wire the prosecutor into bench_skill.py — recurring 2x judge spend to make a
  sentence true when scoping the sentence is free. A fresh backlog issue — a second home for
  #310. Promote the stats menu now — round 2 has not converged; pre-empting it repeats the
  #313 non-convergence.
- Reopen-if: a skill-cell KEEP is overturned by a manual prosecutor pass -> wire it, spend
  earned. #310 closes with the menu unaddressed -> re-file survivors singly.
- Enforced: `skill-bench/skills/bench/references/judging.md` (path scoping); issue #310
  (round-2 set).
