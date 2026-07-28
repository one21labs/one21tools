---
id: 0086
title: "Confirmed failure-mode class FM-1: silent guard-coverage gap; mitigation is guard-liveness instrumentation"
status: accepted
summary: "First confirmed NEW class from the #268 mining study: a wired guard silently fails to fire on part or all of its intended surface — fail-open by design, and nothing watches for non-firing, so discovery is by audit or incident (rung: none). Four independent instances. UNMITIGATED as of 2026-07-27: both decided carriers were deleted (#311), so the class is LIVE and nothing detects it."
---

# 0086 — FM-1: silent guard-coverage gap

- Date: 2026-07-23
- Owner: PM (class confirmed by the pre-registered #268 mining pass, per ADR 0084(e))
- Context: full evidence table in the #268 results comment. Independent instances (>=2 sessions
  each, per 0084(c)): #84/#85 retrospect hook unexecutable (test invoked `bash`, not the real
  path); ADR 0069's pair (hardcoded-path self-skipping hook tests masking a `python`/`python3`
  breakage); #253/#255/#256 (advisory review posting nothing on silent denials, post-edit-gate
  skipping every plugin-scoped skill, budget-edit-guard missing a documented file class); ADR
  0081(d)'s `session-end` series at 0 lines ever since SessionEnd wiring shipped. Adjacent
  variant counted OUT of the bar (red-team): #39 `gates.yml` running but not required on `main`
  — a different, uncovered mechanism.

## Decision
**The class is real and named.** FM-1 = a wired guard (hook, CI check, forcing function) fails
to fire on part or all of its intended surface; the failure is OPEN (fail-open is deliberate
design) and UNMONITORED. Detection rung today: NONE — every instance above was found by owner
audit, muda-audit, retrospect, or incident.

**Mitigation — DECIDED HERE, NEVER BUILT, AND NOW UNBUILDABLE AS SPECIFIED (2026-07-27).** Both
carriers were deleted with their hosts (#311): a liveness readout comparing expected vs observed
firings for boundary-coupled guards, and invocation-path canaries asserting each hook's real path
exists, is executable, and matches on every declared input class. The full spec is in this file's
git history; it is not reproduced here because reproducing a design for deleted machinery is
inventory. **The class is LIVE and nothing detects it.** Rebuilding requires a fresh decision, not
this record.

One part survives independently of any instrument and is the reusable rule:
- **Per-event guards are exempt from silence-inference — by DECLARED classification, never
  per-run judgment.** A deny hook at zero hits is legitimately silent; zero must never be read as
  dead. Boundary-coupled iff the guard fires once per an event independently logged elsewhere;
  per-event-exempt only iff firing is contingent on a condition that may legitimately never occur.
  `session-end` is DECLARED boundary-coupled and DENIED the exemption — it has never fired.

## Justification
Five scars at detection rung NONE is the promotion license ADR 0047 requires. Instrumentation
beats per-guard hardening because each instance looks like a one-off local bug — the recurrence
lives at the coverage-assumption level, which only a cross-guard instrument sees.

## Assumptions
- [unverifiable] WEAKEST — canaries can themselves go vacuous (the ADR 0069 pattern one level up), re-creating FM-1 inside its own mitigation. REOPEN-IF a guard fails silently in a class (a) or (c) claims to cover -> the instrument under-covers; re-scope before trusting it.
- [checkable] the session-end root cause is determinable. result: determined — a FOURTH
  mechanism: the hook file shipped mode 644, so the harness's direct invocation died on
  Permission denied and failed open (the #84/#85 scar class re-instanced inside this ADR's own
  first target). Fix: chmod + the (c) exec-bit canary.
- [checkable] 0086 is free and max+1 on origin/main. result: verified.

## Rejected alternatives
- Liveness as a blocking CI gate — cries wolf on legitimate silence; scorecard is readout-only.
- Inferring per-event guard death from zero hits — zero is the healthy state most windows.
- Per-guard hardening only, no cross-guard instrument — the status quo that produced five
  instances.
- Waiting for a second confirmed instance before acting — the readout is the cheap detector that
  would confirm or kill it.

## Revisit triggers
- The WEAKEST REOPEN-IF fires -> re-scope #276's instrument before trusting any green reading.
- #276's root cause lands on "sessions rarely terminate" -> re-scope the 0081(d) metric to a
  boundary that actually occurs.
- The readout's NOT-FIRING flags exceed ~1/week sustained -> /decide whether to consolidate.
