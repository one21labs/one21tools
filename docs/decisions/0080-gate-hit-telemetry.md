---
id: 0080
title: "Every local gate hit is a logged feedback event: hook-layer append-only telemetry + scorecard breakdown"
status: accepted
summary: "Each local gate hook appends one line to docs/pdca/gate-hits.txt ON FIRING, never in the failure path; scorecard.mjs grows a gate-hits-by-gate readout (no bands until variance is known). CI channel deferred. Gate hits measure corrections CAUGHT at source; defect-escape stays deferred. Executes #246."
---

# 0080 — gate-hit telemetry

- Date: 2026-07-19
- Owner: PM
- Context: gates catch-and-forget — a deny/exit-2 is fed back in-session then lost, so "corrections caught at source" was unmeasured.

## Decision
**(a) Instrument the HOOK layer, not the gate scripts.** A hook fire = a real attempted action caught at source; a bare script run is a pre-flight check, not a correction. Firing points (deny/exit-2 only): `budget-edit-guard`, `post-edit-gate`, `pr-create-guard`, `adr-lint-post-edit`, `explicit-model-guard`. `three-dot-warn` keeps its own session-log channel — not migrated.
**(b) Telemetry never in the failure path** — the append runs after the decision is computed, error-suppressed, and cannot alter the hook's deny output or exit code. Plugin hooks log only where `docs/pdca/` already exists (ADR 0071), never mkdir (ADR 0050).
**(c) Log home + format.** `docs/pdca/gate-hits.txt`, one line per fire: `<ISO-8601 UTC> gate-hit <gate-name> <context>`; `>>` append; `.gitattributes` gets `merge=union` (ADR 0077). Format's one home is `scorecard.mjs`'s `parseGateHits`.
**(d) DELETED 2026-07-27 (#311) — was: a gate-hits-by-gate breakdown, readout, no bands** until variance is known. A malformed line is fail-loud; an absent log post-ship reads as a true ZERO.
**(e) CI-side hits deferred** (mineable from PR history). **(f) ADR 0079 — partial:** ships the CAUGHT-side marker only; defect-ESCAPE still has none.

## Justification
- **NOTE (2026-07-27):** (d)'s breakdown is GONE with `scorecard.mjs` (#311). The log (a)-(c)
  is unaffected, still written on every fire.

Grader-free and mechanical; reuses the existing append-only telemetry pattern; cost ~2 lines per hook plus one pure parser; fully reversible.

## Assumptions
- [unverifiable] WEAKEST — the series' worth rides on it: hook-layer hits track real violation attempts, not harness noise, and zero is a true zero only for hook-mediated work. REOPEN-IF the log shows mechanical duplicate storms dominating the series -> dedupe at parse or demote the instrument.
- [checkable] no touched hook's deny/exit behavior changes when logging is impossible, and each logs exactly one line per fire. result: verified (per-hook suites + `scorecard.test.mjs`'s `parseGateHits` cases).

## Rejected alternatives
- Instrument the gate SCRIPTS — puts telemetry in the decision path; reuse `session-log.txt` — mixes correction events into ambient telemetry; ship bands now, or log from CI — premature/redundant.

## Revisit triggers
- A gate shows recurring hits across sessions -> fire a /decide: move it up the poka-yoke ladder or fix the upstream doc; mint bands from the observed variance.
- A mechanical defect-ESCAPE marker ships -> graduate defect-escape (ADR 0079's trigger).
- Duplicate-storm noise dominates -> the WEAKEST assumption's REOPEN-IF.
