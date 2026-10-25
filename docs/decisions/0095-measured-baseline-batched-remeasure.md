---
id: 0095
title: "Measured means measured-at-baseline; out-of-loop edits accrue to a batched G>=8 re-measure"
status: accepted
summary: "A measured claim means measured at its dated baseline, not HEAD; out-of-loop edits ship freely, tracked by git alone; the debt is paid by a batched hermetic G>=8 re-measure that must precede any new or upgraded measured claim."
---

# 0095 — measured-at-baseline + batched re-measure

- Date: 2026-07-28
- Owner: PM
- Panel: plugin-adopter, process-economist, lean-process-engineer; then verifier, red-team,
  grok-4.5 foreign lane (ADR 0093). Economist dissent (one standing debt issue) rejected below.
- Context: the README paired-eval promise was unconditional; ADR 0024 decision 2(d) requires a
  re-measure only per improvement-loop iteration, and no gate fires on an unmeasured edit
  (`.github/workflows/gates.yml`). Measured 28-Jul-2026: 8 content commits since the 2026-07-18
  baselines, none re-measured.

## Decision
1. A "measured" claim means measured AT the dated baseline dir the README measured-state block
   cites — never at HEAD. **The obligation is owed to the CLAIM, not to the edit:** an
   out-of-loop edit owes nothing when it ships.
2. Out-of-loop edits ship without a re-measure. `git log --since=<baseline-date> --
   <source>/<name>` IS the ledger — the WHOLE skill dir under its plugin source (scripts and evals
   count). No ledger file, no standing issue. Git is not immutable (rewritten 27-Jul): the
   rewrite-proof anchor is CONTENT — a paired run commits `treatments/<skill>*.txt`, byte-compared
   against the live body.
3. Debt is paid by a BATCHED hermetic re-measure at G>=8 evals. Forcing function: a PR that adds,
   upgrades, or restates-after-drift a measured claim for skill S — on ANY claim surface (README
   block, pdca-workflow/README.md Measured, one21labs/skill-measure:README.md) — must cite a benchmark dir
   whose committed treatment byte-matches the shipped body (a dir DATE is not provenance; it
   misfires on same-PR revise-and-re-measure, e.g. da76cbc), and the PR body pastes that check's
   output — merges here are self-merges in minutes. Baselines are per-CLAIM, not per-skill.
4. A batch below 8 post-prescreen evals is DIAGNOSTIC ONLY: it may retire a claim or mark it
   UNDERPOWERED; it never discharges debt for a KEEP or an upgrade. A batch that authors new evals
   records the eval-set diff vs the cited baseline and, while #317 is open, the
   skill-expectation overlap number; a changed instrument never renders as a trend.
5. The README headline carries its true scope; the measured block holds no hand-maintained
   counters (a dated baseline never rots, an edit count does).
6. ADR 0024 decision 2(d) governs the IN-loop case, unchanged. An edit is in-loop iff it ships
   with the benchmark dir that measured it; every other edit under the skill's dir is out-of-loop
   debt by path.

## Justification
Per-edit re-measurement is underpowered: MDE 0.24-0.37 at G=6 (closed form `(t95(G-1)+t80(G-1))*se`,
the `mde80` field of `benchstats.keep_verdict()`) against July deltas of +0.009..+0.27, so ~$63
buys likely-INCONCLUSIVE verdicts; scoping the promise deletes the overclaim instead of building
machinery to service it.

## Assumptions
- [checkable] **WEAKEST:** 8 discriminating evals per skill are reachable at all; if not, decision
  4 makes this record indistinguishable from "never re-measure". owner: the first batched
  re-measure; result: pending — named signal: that batch's post-prescreen G, in its benchmark dir.
- [verified] all four measured skills' batteries held exactly 6 evals (`skills/<name>/evals/evals.json`),
  so G>=8 requires AUTHORING evals.
- [verified] no gate fires on an unmeasured edit (`.github/workflows/gates.yml`).
- [checkable] git history alone reconstructs each skill's unmeasured-edit set — owner: PR review;
  result: verified (`git log --since=2026-07-19 -- skills/`: the 8 content commits + 8d698bc).
- [unverifiable] the MDE generalizes to these skills' true effect sizes — REOPEN-IF a G>=8 batch measures a single-edit effect >=0.35; per-edit re-measurement then regains its value.

## Rejected alternatives
- Re-measure all now at G=4-6 — ~$63 for INCONCLUSIVE verdicts; code-standards had zero edits.
- Revert the unmeasured edits — reintroduces known-false claims later commits fixed (40cd021).
- A standing debt ledger (file or issue) — a second home for what git records; the un-gated
  tracker shape already deleted once (issue #311).
- A mechanical CI gate on unmeasured edits now — no instance yet; revisit trigger 1 buys it.

## Revisit triggers
- A measured claim ships whose cited dir did not measure the shipped content -> escalate to a
  mechanical gate (predicate: treatment-vs-live-body byte-compare).
- The first batch cannot reach 8 discriminating evals -> decide: invest in eval authoring, or
  retire that skill's measured claim.
- ADR 0024's loop runs on a skill with unpaid out-of-loop debt -> fold the batch into iteration 1.
- `keep_verdict` renders a bare KEEP below 8 clusters -> add the engine floor, not more prose.
