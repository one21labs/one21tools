---
id: 0080
title: "Every local gate hit is a logged feedback event: hook-layer append-only telemetry + scorecard breakdown"
status: accepted
summary: "Each local gate hook appends one line to docs/pdca/gate-hits.txt ON FIRING (deny/exit-2), never in the failure path; scorecard.mjs grows a gate-hits-by-gate readout (no bands until variance is known). CI channel deferred (mineable from PR history). Gate hits measure corrections CAUGHT at source; defect-escape stays deferred (needs an escape-side marker). Executes #246."
---

# 0080 — gate-hit telemetry

- Date: 2026-07-19
- Owner: PM
- Panel: none — routine/reversible tooling call, shape owner-proposed in #246 (ADR 0062 two-stage: no panel); ships, so the fresh `verify` gate ran (step 6).
- Context: gates catch-and-forget — a deny/exit-2 is fed back in-session, then lost; no committed series exists, so "corrections caught at source" (the mechanical correction marker ADR 0079 (b) lacked) is unmeasured. Precedent in-tree: `three-dot-warn.sh` already logs its fires to make its promotion window measurable.

## Decision
**(a) Instrument the HOOK layer, not the gate scripts.** A hook fire = a real attempted action caught at source (a correction event); a bare script run is a pre-flight check, not a correction — and gate scripts' parse/decide logic stays pure and tested. Firing points (deny or exit-2 only): `budget-edit-guard`, `post-edit-gate` (logs the failing gate's basename: validate.py / check-workflow.mjs / check-restatement.mjs), `pr-create-guard` (context = sub-guard), repo + plugin `gate-pipe-guard`, `adr-lint-post-edit` (logs `adr-lint`), `explicit-model-guard`. `three-dot-warn` keeps its settled session-log channel (warn rung, ADR 0072's promotion count reads it) — not migrated.
**(b) Telemetry never in the failure path.** The append runs after the decision is computed, error-suppressed, and cannot alter the hook's deny output or exit code; a logging failure must never break (or un-break) a gate. Plugin hooks log only where `docs/pdca/` already exists (ADR 0071 marker) and never mkdir (ADR 0050); repo hooks carry the same guard for testability.
**(c) Log home + mechanics inherit the session-log doctrine.** `docs/pdca/gate-hits.txt`, one line per fire: `<ISO-8601 UTC> gate-hit <gate-name> <context>`; single-line `>>` append (atomicity rationale: `spawn-log.sh` header); `.gitattributes` gains `merge=union` for it (ADR 0077's reasoning applies identically). The line format's ONE home is `scorecard.mjs` `parseGateHits` — hooks cite it, no format doc.
**(d) scorecard.mjs grows a gate-hits-by-gate breakdown — readout, no bands.** The metrics-engine.md ratioMetric shape ("Gate Hit" by dimension) as a read-out row; bands/thresholds mint only once variance is known (revisit trigger below). A malformed log line is fail-loud: listed, folded into the PARTIAL verdict, never dropped. An absent log post-ship reads as ZERO hits (a true reading, stated as such), not as uninstrumented.
**(e) CI-side hits: separate channel, DEFERRED.** gates.yml failures are already mineable from PR history; committing telemetry from CI runners is a new mechanism with new failure modes — rejected until local data proves the series worth widening.
**(f) ADR 0079 trigger ruling.** The marker shipping here is the CAUGHT-side correction marker: "corrections caught at source" becomes a measured series now. Defect-ESCAPE (a defect past the gates) still has no mechanical marker — it stays NOT INSTRUMENTED, reason sharpened in `SCORECARD_CONFIG.deferred`. 0079's "marker ships → build defect-escape" trigger therefore fires only partially; the escape side still gates on its own marker.

## Justification
Grader-free and mechanical (the gaming vector 0079 rejected stays closed); reuses the existing append-only telemetry pattern instead of a new mechanism; cost ≈2 lines per hook + one pure parser; fully reversible (delete the appends, the file, the rows). The alternative altitudes both fail: script-level logging pollutes pre-flight runs and puts IO in tested pure logic; CI-level logging needs commit machinery.

## Assumptions
- [unverifiable] WEAKEST — the series' worth rides on it: hook-layer hits track real violation attempts (a faithful corrections-caught-at-source proxy), not harness noise — a retried edit or an agent loop could double-log the same violation; and zero is a true zero only for HOOK-MEDIATED work (a hermetic `claude -p` run or out-of-session edit contributes no fires) — cross-family review flagged both. REOPEN-IF the log shows mechanical duplicate storms (same gate+context, seconds apart) dominating the series → dedupe at parse or demote the instrument.
- [checkable] no touched hook's deny/exit behavior changes when logging is impossible (no `docs/pdca/`, unwritable file) — owner: verifier + per-hook test suites. result: verified — marker-absent cases are automated in every touched suite (explicit-model-guard's in its `.test.mjs`); the unwritable-log case the fresh verifier reproduced manually (byte-identical deny/exit across writable, log-as-directory, chmod-0), and the appends run in a stderr-silenced brace group so even a redirection-open failure leaks nothing.
- [checkable] every touched hook logs exactly one line per fire and none on pass — owner: per-hook test suites + scorecard.test.mjs (`parseGateHits` cases). result: verified — suites + `node --test` green locally.
- [checkable-doc] no settled ADR contradicted: 0071 (marker check kept, no mkdir), 0077 (union-merge extended, not altered), 0072 (three-dot-warn channel untouched), 0079 (b) (readout-first honors "bands once variance is known"), 0047 (every touched hook keeps a CI-visible test). result: verified against each cited ADR.

## Rejected alternatives
- Instrument the gate SCRIPTS (adr-lint.mjs, validate.py, …) — telemetry in the decision path; logs pre-flight runs as corrections; breaks the pure-parse test design.
- Reuse `session-log.txt` — mixes correction events into ambient session telemetry; one file per consumer stays clean (scorecard reads gate-hits; retrospect reads session-log).
- Ship bands / a "recurring hit fires /decide" threshold now — variance unknown; premature machinery. The rule lives as a revisit trigger until data exists.
- Log from CI (workflow commits back to the repo) — new mechanism, new failure modes, redundant with PR history.

## Revisit triggers
- A gate shows recurring hits across sessions → fire a /decide: move that rule up the poka-yoke ladder (detect → prevent) or fix the upstream doc — and mint bands in `SCORECARD_CONFIG` from the observed variance (the #246 graduation). Banding needs an ATTEMPTS denominator story first: a raw hit count without exposure cannot band honestly.
- A mechanical defect-ESCAPE marker ships → graduate defect-escape (continues 0079's trigger).
- The local series proves decision-useful and the CI channel is wanted → design CI-side mining as a separate readout (never runner commits).
- Duplicate-storm noise dominates → the WEAKEST assumption's REOPEN-IF.
