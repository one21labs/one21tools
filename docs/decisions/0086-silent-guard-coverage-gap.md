---
id: 0086
title: "Confirmed failure-mode class FM-1: silent guard-coverage gap; mitigation is guard-liveness instrumentation"
status: accepted
summary: "First confirmed NEW class from the #268 mining study (method: ADR 0084): a wired guard silently fails to fire on part or all of its intended surface — fail-open by design, and nothing watches for non-firing, so discovery is by audit or incident (rung: none). Four independent instances 07-10 through 07-23, plus one adjacent enforcement-config variant. Mitigation (instrument-first, 0084(f)): boundary-coupled liveness readout in scorecard + per-declared-input-class canaries in check-gate-tests; build deferred to #276, whose acceptance requires flagging the live instance (the empty session-end series, declared boundary-coupled). Undeclared partial-surface gaps stay at rung NONE — stated, not claimed watched."
---

# 0086 — FM-1: silent guard-coverage gap

- Date: 2026-07-23
- Owner: PM (recording a class confirmed by the pre-registered #268 mining pass, per ADR 0084(e) record-when-found)
- Panel: none — the class promotion follows 0084's pre-registered bar mechanically; a fresh red-team ran on this record before ship (ADR 0062): no blocking break, 2 FOLD + 2 NOTE, all folded below.
- Context: the study's full evidence table lives in the #268 results comment (23-Jul-2026). Instances, grouped to >=2-independent-sessions per 0084(c): #84/#85 retrospect hook unexecutable, masked by its test invoking via `bash` not the real path (07-10); ADR 0069's pair — hardcoded-path self-skipping hook tests masking a real `python` vs `python3` breakage (07-15/16); #253 + #256 + #255 — advisory review posting nothing on silent permission denials, post-edit-gate skipping every plugin-scoped skill, budget-edit-guard missing a file class its docs claimed (one session, 07-19/20, counted once); the ADR 0081(d) `session-end` series at 0 lines ever despite SessionEnd wiring shipped 07-19, re-verified empty 07-23. Adjacent variant, counted OUT of the bar (red-team): #39 `gates.yml` running but not required on `main` (07-08) — "runs but unenforced" is an enforcement-config gap, a different mechanism this ADR's instruments do not cover. ADR 0069 mitigated only the TEST-vacuity sub-class; production firing-coverage stayed unwatched.

## Decision
**The class is real and named.** FM-1 = a wired guard (hook, CI check, forcing function) fails to fire on part or all of its intended surface; the failure is OPEN (fail-open is deliberate design, ADR 0060 et al.) and UNMONITORED (no rung watches whether firing happens at all). Its detection rung today is NONE — every instance above was found by owner audit, muda-audit, retrospect, or incident.

**Mitigation (instrument-first, per 0084(f)) — decided here, built under #276:**
- **(a) Boundary-coupled liveness readout** in `scripts/scorecard.mjs` (readout only, never a CI gate — ADR 0079(a)): for guards whose firing couples to a countable boundary, compare expected vs observed — `session-end` lines vs distinct Claude-Session evidence in the window; muda-review comments vs merged PRs. Wired + expected>0 + observed=0 prints NOT FIRING.
- **(b) Per-event guards are exempt from silence-inference — by DECLARED classification, never per-run judgment.** A deny hook at zero hits is legitimately silent (no over-cap attempt happened); zero must never be read as dead. The mechanical test (red-team fold): boundary-coupled iff the guard should fire once per an event independently logged elsewhere; per-event-exempt only iff firing is contingent on a condition that may legitimately never occur. The classification is a per-guard declaration the readout consumes, so the exemption cannot be argued case-by-case to swallow a dying guard.
- **(c) Invocation-path canaries** in `scripts/check-gate-tests.mjs`: every wired hook's REAL invocation path is asserted — file exists at the registered path, is executable, and its matcher fires on a synthetic representative of EACH input class the guard itself declares (its case-match arms / documented coverage list — the enumerable surface #255's "docs claimed" gap shows must be tested per-class, not per-guard). Generalizes ADR 0069 from "tests must not self-skip" to "registration must provably reach the script on every declared class".
- **(d) First target and acceptance criterion:** `session-end` is DECLARED boundary-coupled (expected = distinct Claude-Session evidence in the window) and is DENIED the (b) exemption — readout (a) must flag it until it either fires or ADR 0081(d) is re-scoped. #276 must flag and root-cause it (candidates: hook never fires; sessions rarely terminate cleanly, one span was 6 days; parent-cwd sessions load no project hooks, #268's unconfirmed hypothesis), then fix or re-scope.
- **(e) Residual, stated plainly (red-team fold):** partial-surface non-firing in a guard with NO enumerable surface declaration remains at rung NONE. This ADR narrows the class's unwatched region; it does not claim to eliminate it.

Falsifiable criterion: after #276 ships, a wired boundary-coupled guard that stops firing is surfaced by the next scorecard run, and a wired hook that is unreachable — or dead on any DECLARED input class — fails check-gate-tests in CI. Neither waits for an incident. Non-firing on an undeclared sub-surface is out of scope per (e).

## Justification
Five scars across >=5 sessions with detection rung NONE is the exact promotion license ADR 0047 requires; the ladder's own premise ("a stale hook enforcing retired policy" is the loop's characteristic failure, ENGINEERING_PRINCIPLES Process-Level Poka-yoke) predicted this class before the study confirmed it. Instrumentation beats per-guard hardening because the class's signature is that each instance looks like a one-off local bug — the study shows the recurrence lives at the coverage-assumption level, which only a cross-guard instrument sees.

## Assumptions
- [unverifiable] WEAKEST — canaries can themselves go vacuous (the ADR 0069 pattern one level up): a canary that self-skips would re-create FM-1 inside its own mitigation. Bounded, not eliminated, by canaries living in check-gate-tests (rung 4, CI-visible, itself test-covered). REOPEN-IF a guard fails silently in a class (a) or (c) claims to cover -> the instrument under-covers; re-scope before trusting it again.
- [checkable] the session-end root cause is determinable and one of the three named candidates. owner: #276. result: pending — if it is "sessions rarely end", the fix is re-scoping 0081(d)'s metric, not repairing the hook.
- [checkable-doc] no settled ADR contradicted: 0069 extended not re-litigated; 0079(a) readout-only honored; 0080(d) absent-log semantics honored; 0047 promotion licensed by cited scars; 0084(e)/(f) followed. result: verified.
- [checkable] 0086 is free and max+1: highest on origin/main is 0085. owner: PM. result: verified.

## Rejected alternatives
- Liveness as a blocking CI gate — absence is ambiguous for event-driven series; a gate would cry wolf on legitimate silence (precondition (ii) of ADR 0047) and scorecard is readout-only by settled decision (0079(a)).
- Inferring per-event guard death from zero hits — zero is the healthy state most windows; the inference is structurally unsound (decision (b)).
- Per-guard hardening only, no cross-guard instrument — that is the status quo that produced five instances; each fix was correct and the class recurred anyway.
- Waiting for a second confirmed instance of the parent-cwd hypothesis before acting — the liveness readout is exactly the cheap detector that would confirm or kill it; instrument-first is 0084(f)'s named policy.

## Revisit triggers
- The WEAKEST REOPEN-IF fires (a silent guard failure inside claimed coverage) -> re-scope #276's instrument before trusting any NOT-FIRING/green reading.
- #276's root cause lands on "sessions rarely terminate" -> the 0081(d) compliance metric needs re-scoping to a boundary that actually occurs; record that change in 0081 itself with a back-pointer, never silently here.
- The readout's NOT-FIRING flags exceed ~1/week sustained -> the repo's guard surface is outrunning its instrumentation; /decide whether to consolidate guards before adding more.
