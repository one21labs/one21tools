---
id: 0086
title: "Confirmed failure-mode class FM-1: silent guard-coverage gap; mitigation is guard-liveness instrumentation"
status: accepted
summary: "FM-1: a wired guard silently fails to fire on part or all of its surface — fail-open by design, unmonitored, detection rung NONE. Four independent instances. Both decided carriers were deleted (#311): the class is LIVE, nothing detects it, and a rebuild needs a fresh decision."
---

# 0086 — FM-1: silent guard-coverage gap

- Date: 2026-07-23
- Owner: PM (class confirmed by the pre-registered #268 mining pass, ADR 0084(e))
- Context: evidence table in the #268 results comment. Independent instances (>=2 sessions each,
  0084(c)): #84/#85 retrospect hook unexecutable (test invoked `bash`, not the real path); ADR
  0069's hardcoded-path self-skipping hook tests; #253/#255/#256 (silent advisory review,
  post-edit-gate skipping plugin skills, budget-edit-guard missing a file class); ADR 0081(d)'s
  `session-end` series at 0 lines. Counted OUT: #39 `gates.yml` not required on `main` — a
  different mechanism.

## Decision
**The class is real and named.** FM-1 = a wired guard (hook, CI check, forcing function) fails
to fire on part or all of its intended surface; the failure is OPEN (deliberate design) and
UNMONITORED. Detection rung: NONE — every instance was found by audit, retrospect, or incident.

**Mitigation: unbuilt and unbuildable as specified.** Both decided carriers — a liveness readout
(expected vs observed firings for boundary-coupled guards) and invocation-path canaries — were
deleted with their hosts (#311); spec in git history. **The class is LIVE and nothing detects
it.** A rebuild requires a fresh decision, not this record.

**(b) The surviving rule: per-event guards are exempt from silence-inference — by DECLARED
classification, never per-run judgment.** A deny hook at zero hits is legitimately silent.
Boundary-coupled iff the guard fires once per an event independently logged elsewhere;
per-event-exempt only iff firing is contingent on a condition that may legitimately never occur.
`session-end` is DECLARED boundary-coupled and DENIED the exemption.

## Justification
Five scars at detection rung NONE is the promotion license ADR 0047 requires; each looks like
a one-off local bug, so the recurrence lives at the coverage-assumption level, which only a
cross-guard instrument sees.

## Assumptions
- [unverifiable] WEAKEST — canaries can themselves go vacuous (the ADR 0069 pattern one level up), re-creating FM-1 inside its own mitigation. REOPEN-IF a guard fails silently in a class a rebuilt instrument claims to cover -> re-scope before trusting it.
- [checkable] the session-end root cause is determinable. result: determined — the hook shipped mode
  644, so the harness's direct invocation died on Permission denied and failed open (the #84/#85
  class again); fix: chmod.

## Rejected alternatives
- Liveness as a blocking CI gate — cries wolf on legitimate silence.
- Inferring per-event guard death from zero hits — zero is the healthy state most windows.
- Per-guard hardening only — the status quo that produced these instances.
- Waiting for another instance before acting — the readout was the cheap detector that would decide it.

## Revisit triggers
- A new FM-1 instance is confirmed, or the WEAKEST REOPEN-IF fires -> /decide the rebuild.
