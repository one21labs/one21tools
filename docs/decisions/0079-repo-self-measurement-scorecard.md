---
id: 0079
title: "Repo self-measurement scorecard: north-star as compass, ship a gated hit-rate + a mechanical reference-veracity hook, defer graders + Level-1"
status: accepted, superseded in part (#311)
summary: "Operationalize the README goal as a COMPASS (corrections/shipped-work at cost), not a gate — flagged for owner confirmation. Ship the assumption hit-rate (first metrics-engine.md implementation) + reference-veracity as a mechanical PR-diff hook. Accept DERIVED/CITED/MEASURED routing as doctrine. Defer every grader-needing rate and Level-1 (design in #236, gated on PR #219). SUPERSEDED IN PART 2026-07-27: the hit-rate half (scorecard.mjs) was deleted for gating nothing and never being invoked by CI (#311), so the repo measures itself with nothing; the reference-veracity hook is live and mutation-verified."
---

# 0079 — repo self-measurement scorecard

- Date: 2026-07-18
- Owner: PM
- Context: owner wants the README goal measured (issue #240); metrics are gates, not optimization
  targets.

## Decision
**(a) North-star = compass, not a gate — owner-confirmation pending.** "Corrections per unit
shipped work, at cost" has no direct sensor; gating it means gating a mirror of its inputs.
Numerator from committed artifacts only, never transcripts. Live proxies = (b)'s two instruments.

**(b) Ship a gated hit-rate + a mechanical reference-veracity hook; defer/reject the rest.**
- SHIP — assumption hit-rate (`scripts/scorecard.mjs`): **DELETED 2026-07-27 — never invoked by
  CI, gated nothing (#311); the hit-rate is unmeasured and the corpus has no self-measurement.**
  Spec in this file's git history (reproducing a design for deleted machinery is
  inventory, ADR 0086); re-decide before rebuilding.
- SHIP — reference-veracity as a mechanical PR-diff hook: a diff adding an external URL/arXiv-ID
  to a tracked corpus path must also touch a `sources/*-reference-audit*` record. Mechanizes
  because the trigger is syntactic; the fetch-audit's truth stays the manual adversarial step.
- DEFER — defect-escape, owner-intervention rate, summary-truthfulness spot-audit (each needs a
  grader or an unminted marker); the periodic re-audit sweep (the write-time hook is primary).
  REJECT as gates — cycle-time, cost-per-decision. Epistemic routing (DERIVED/CITED/MEASURED)
  is doctrine text in `metrics-engine.md`, not a classifier.

**(c) Level-1 vs-alternatives — design-and-defer.** Blocked on PR #219 (orchestration plugins
can't run under hermetic tool-denied `claude -p`); derived cost $360-480 fails the recorded-miss
bar. Design records in #236; execution gated on #219 resolved AND a battery adopted.

## Justification
Every shipped item was grader-free and mechanically enforced until the (b) deletion; every
deferred item needs a grader that is itself the gaming surface it would introduce.

## Assumptions
- [unverifiable] WEAKEST: hit-rate + reference-veracity move WITH the real trust gap (owner corrections per shipped PR) while the direct corrections numerator stays deferred. REOPEN-IF the owner records a correction neither instrument anticipated, OR the coverage row degrades below its band, OR a mechanical defect marker diverges from the proxies.

## Rejected alternatives
- Gate the north-star composite directly — no direct sensor; gates a mirror of its inputs.
- Reference-veracity as a manual doc-rule / human defect-escape label — suppressible self-reports.

## Revisit triggers
- Owner rules the north-star must be a hard gate -> re-open (a).
- Owner records an unanticipated correction, or the coverage row drops below its band -> re-open
  the WEAKEST proxy-faithfulness assumption.
- The reference-veracity hook is bypassed or a citation miss recurs -> escalate the hook.
- PR #219 resolved AND a task battery adopted -> run the Level-1 pilot, then set a ceiling.
