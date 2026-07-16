---
id: 0068
title: "Retrospect friction channel: Phase-0 kill test before any ledger/blind-first machinery"
status: accepted
summary: "Route #189's hypothesis (mechanical friction ledger + blind-first ordering beat orchestrator-curated summaries) through a zero-spend Phase-0 test on existing session transcripts. Ledger ships only if it surfaces curated-omitted, finding-grade friction; blind-first ordering additionally requires an ADR 0024 measured run. A Phase-0 null closes #189 with no machinery."
---

# 0068 — retrospect friction channel: gate before machinery

- Date: 2026-07-15
- Owner: PM
- Panel: none — routine, reversible process-instrumentation call; recorded directly per ADR
  0062's two-stage routing. **This is a hypothesis to be tested and falsified, not a
  conclusion (ADR 0059).**
- Context: /retrospect's friction channel is orchestrator-curated — the session driver
  hand-writes the friction summary the retrospect agent receives, so the reviewed party
  curates the evidence against itself (#189, owner-surfaced 2026-07-14: 7 of 9 retro threads
  traced to the orchestrator's list and adopted its framings; the one fully novel finding came
  from the agent's independent git read). Candidate redesign: (1) a mechanical friction ledger
  — deterministic extract of tool errors, hook denials, and nonzero exits already present in
  the harness transcript JSONL (or a hook appending to the `docs/pdca/session-log.txt`
  pattern); (2) blind-first ordering — retrospect pass 1 reads only the git range, the ledger
  arrives in pass 2. Both may fail their own bars: the ledger could be noise-dominated (every
  benign retry logged) and two passes cost more than one.

## Decision
1. **Phase 0 — zero new generation, pre-registered before analysis.** Over the 5 most recent
   sessions with a recorded retrospect run: build the mechanical ledger from each session's
   transcript JSONL and compare it against the curated friction list that session's retrospect
   agent actually received (recorded in the spawn prompt). Frozen question: does the ledger
   surface at least one FINDING-GRADE friction item (routable to a home; benign retries and
   self-corrected typos excluded) that the curated list omitted, in at least 3 of 5 sessions?
   Below threshold -> hypothesis falsified for the ledger, recorded null, #189 closes, no
   machinery ships. Named confound: "finding-grade" is judged post-hoc — classify items
   blind to which channel produced them.
2. **Phase 1 — only if Phase 0 passes.** The LEDGER ships first (cheapest structural piece —
   a deterministic extract or hook, poka-yoke before process, the ADR 0062 d3 shape); its
   pre-registration follows ADR 0065 (gate-or-optimization field, pre-screen, variance, MDE)
   and ADR 0066 (grading-cost estimate) if any grading spend is involved. **Blind-first
   ordering is a separate, costlier claim:** it changes the retrospect flow and must clear an
   ADR 0024 measured run (I1-v2 instruments precedent) before adoption — never on assertion,
   even with a Phase-0 pass in hand.
3. Phase-0 execution and its verdict live on #189 (the tracking issue); the analysis artifact
   lands in a dated dir per the benchmark conventions if it grows beyond a comment.

Falsifiable criterion: Phase 0's frozen question above — a miss in 3+ of 5 sessions kills the
ledger claim; a blind-first adoption without a measured run reopens this ADR.

## Justification
The bias mechanism is structural (agenda-setting by the reviewed party), but the remedy's
value is an empirical claim about what the ledger ADDS — and the data to test it already
exists, so the cheap gate precedes any build (ADR 0062 d2 doctrine; #186's Phase-0 shape,
which killed-or-confirmed for ~$0). Building first would be adopt-on-assertion (ADR 0024).

## Assumptions
- [verified] the curation-bias observation base: #189 records 7/9 retro threads tracing to
  the orchestrator's list, with the one novel finding from the agent's independent git read.
- [checkable] harness transcript JSONL carries extractable tool errors/hook denials/nonzero
  exits sufficient to build the ledger without new instrumentation. TEST: the Phase-0 extract
  itself. — owner: Phase-0 run, on #189. result: confirmed 2026-07-15 —
  benchmarks/2026-07-15-pdca-retrospect-friction-phase0/ (PASS 3/5 at threshold).
- [unverifiable] blind classification adequately controls the hindsight confound in
  "finding-grade" — REOPEN-IF the Phase-0 verdict flips under an independent second
  classification pass.

## Rejected alternatives
- **Build ledger + blind-first now** — adopt-on-assertion; the exp-3/exp-4 lesson is that
  plausible mechanism claims routinely fail measurement.
- **Decline** — leaves a structural bias in the one process instrument the repo uses on every
  PR; the only independent channel produced the only novel finding.
- **Measure blind-first before the ledger gate** — inverts the two-stage doctrine: the
  expensive powered claim would run before the free gate.

## Revisit triggers
- Phase 0 passes -> Phase-1 ledger pre-registration (ADR 0065/0066 rules) before any
  retrospect skill or hook edit.
- Phase 0 null -> close #189 as a recorded null; the curated channel stays, with no caveat
  machinery added (a null earns no hedge text).
