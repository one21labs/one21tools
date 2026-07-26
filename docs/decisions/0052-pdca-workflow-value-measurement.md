---
id: 0052
title: "PDCA-workflow value measurement: both instruments, shared plumbing pilot, cost-gate as hard stop"
status: accepted
tier: lite
summary: "Execute #172's two value instruments as pre-registered (retrospect recall + /decide three-arm outcome): a shared plumbing pilot precedes either grid; the I2 cost-pilot is a HARD stop via a cost-gate; blind.py homes in one lib. Committed pre-regs before spend are the checkable artifact."
---

# 0052 — PDCA-workflow value measurement plan

- Decision: execute both #172 value instruments as pre-registered — I1 retrospect recall, I2
  `/decide` three-arm outcome (keep arm B, cost-matched unstructured: the without-arm alone
  measures spend, not structure). One shared plumbing pilot precedes EITHER grid (both arms' C
  need the same deny-list carve-out + plugin load). I2's cost-pilot is a HARD stop: a cost-gate
  exits nonzero if projected grid cost exceeds the pre-registered ceiling (each pilot's gate
  firing reset the ceiling via a fresh /decide — I1 to $30, I2 to $300). `blind.py` normalization
  homes in one lib, not a 10th dated-dir copy. Both pre-regs committed BEFORE any grid spend.
- Why: I1 is cheap/objective and de-risks I2's pipeline; I2 is the flagship's only outcome-level
  evidence. Each fix is the cheapest available option, discharging ADR 0042's overspend pattern
  (216 cells run past a decidable gate).
- Rejected: I1 as a plumbing-free warm-up (false — both arms need the same carve-out); cost-pilot
  as an advisory, non-halting gate (ADR 0042 shows that pattern overspent once).
- Reopen-if: the plumbing pilot's arm C cannot load the panel/skill or leaks isolation -> halt,
  reopen whether a non-hermetic directional run is worth recording. C~B on the outcome grid ->
  route to its own /decide, don't silently keep the claim.
- Enforced: `benchmarks/lib/verdict.py`, `benchmarks/lib/bench_io.py`; pre-registrations committed
  under each dated `benchmarks/2026-07-*-pdca-*` dir.
