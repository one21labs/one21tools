---
id: 0061
title: "Operationalize the #172-gating experiments: #186 Phase-0 DoD-check + #185 poker arm P"
status: accepted
summary: "Operationalize the owner-frozen #186/#185 pre-regs: norm input + dual-family classifier + within-arm three-state; framer-fixed options, 3 reps + MDE, fresh A, $150 gate, bar-c outcome spread; Phase-1 not a #172 gate."
---

# 0061 — Priority experiments (#186 Phase-0, #185) operationalization

- Date: 2026-07-14
- Owner: PM
- Panel: process-economist (spend), session-operator (harness), lean-process-engineer (metric validity) — the benchmark-design trio.
- Context: #172 closure gates on the two frozen pre-regs. Both corpora graded and verified (72+72 cells). Frozen: #186 kill = within-arm DoD-pass beats DoD-fail on fraction-met by >=0.15 in BOTH corpora else falsified/STOP/null; #185 four bars under dual-judge, prompts frozen.

## Decision
**#186 Phase-0 (zero-generation-spend):**
- 1a Input = **norm** (arm-blind substrate; raw begs H1 via arm-C scaffolding).
- 1b **Dual-family** on the two model items (subject-matter assumption; failure class); items 3-4 mechanical/regex, no model. Cross-family disagreement on DoD-pass/fail -> EXCLUDE + record. Verdict pivot (0057 d2).
- 1c **Within-arm, within-corpus** (never pool). Floor **n>=5 both buckets**, set BLIND (no peeking — 0042). Three states: both>=5 -> apply the owner's >=0.15 test (SUPPORTED/FALSIFIED); either bucket <5 or >90%-skew -> **INCONCLUSIVE** (absence-of-data, never falsification).
- 1d Kill = **full fraction-met** (owner freeze). ADD a pre-registered DIAGNOSTIC: same delta on the non-ceilinged subset (exps 3-4; exps 1-2 sit at 0.92 ceiling, `benchmarks/2026-07-12-pdca-decide-outcome/README.md:141`, diluting a real delta). Diagnostic informs a REOPEN, never overrides the kill. Do NOT import #185's "hard-pair".

**#185 (poker arm P vs fresh C vs bare A):**
- 2a **Framer required** — one call/scenario (not per rep), ENUMERATES options only (no scores/rank). Spread + round-2 need a common set; independence kept on score/crux/dependency.
- 2b **3 reps** (armd). MDE stated: full ~0.09, hard-pair ~0.17 (armd cluster-CI half-widths at 3 reps). Bar (a)'s 0.05 margin is INSIDE the noise band — confidence language.
- 2c **Fresh A** (~$14) — same-run rule (`benchmarks/2026-07-13-pdca-decide-armd/README.md:21`, never compared across runs).
- 2d Ceiling **$150** (reuse armd). Cost-pilot before grid (0042): cap **$10**, 3 P cells per the `grid_armd.py` --pilot pattern. re-project the gate on the pilot P mean (armd MEASURED C $4.052, `results.json`).
- 2e Round 2 re-estimates ONLY spread>=2 options (conditional round-2 = P's economic case). Pilot reports fire-rate; herding audit = per-advisor round1->round2 delta, flag convergence to mean/one advisor.
- 2f **Two DISTINCT spreads** (C emits no 1-5 scores): REVEAL SPREAD (P-internal per-option score, drives round-2, never P-vs-C) vs OUTCOME SPREAD (rep-to-rep fraction-met). Bar (c) P<=C uses OUTCOME SPREAD ONLY — the sole P-vs-C-computable metric.
- 2g **sonnet** all P calls (I2 held; a cheaper tier confounds structure-vs-model, corrupts bar b). Strict JSON {score,crux,dependency}; <2/3 usable = ERROR cell (armd probe-floor). Reuse the same 8 scenarios a THIRD time (twice-graded ground truth; staleness named-not-measured, `README.md:12`).

**Sequencing:** Phase-0 (free) runs now; #185 in parallel. **#186 Phase-1 = follow-up, NOT a #172-closure gate** (new spend reopens a deferred question; #172 closes on Phase-0 + #185 verdicts). ADR 0057's plateau cut-vs-keep WAITS for #185 P data — deciding pre-verdict = adopt-on-assertion (0024/0057 forbid).

## Justification
Each call is cost x validity; owner freeze held — fraction-met kills #186 (secondary diagnoses only); #185's bars + dual-judge + frozen prompts inherit verbatim.

## Assumptions
- [checkable] WEAKEST — the #186 verdict pivots here: the DoD-pass/fail classification is itself reliable, NOT judge-sensitive (0057's failure mode). TEST = cross-family disagreement rate, both corpora; disagreement cells excluded. owner: verifier. result: verified (Act).
- [checkable] norm preserves DoD structure (no arm-C scaffolding leak) corpus-wide — spot-check ~5 records/corpus. owner: verifier. result: verified.
- [verified] arm C emits ADRs not 1-5 tables (bar c on OUTCOME spread only); same-run rule armd README:21; cost figures per 2d.
- [checkable-doc] no ADR contradicted: inherits 0024/0025/0042, 0057 d2 (proposed) — adopt-on-assertion; fraction-met; cost-pilot/pre-reg; dual-judge. result: verified.
- [unverifiable] third-reuse scenario staleness doesn't distort outcomes — REOPEN-IF a scenario shows arm-independent drift.
- [unverifiable] P variance stays <= C's despite round-2 — REOPEN-IF pilot P variance exceeds C's (recompute MDE).

## Rejected alternatives
- Single-family + spot-check — underpowers one-directional judge bias.
- Pull actual bucket counts before the floor — violates pre-reg blindness (0042).
- Degenerate split = falsified — conflates absence-of-data with tested-and-failed.
- Hard-pair as #186's kill — silently swaps the owner-frozen kill; kept as diagnostic.
- Self-propose options — spread + round-2 trigger uncomputable.
- Reuse arm A / a reveal spread for bar c — cross-run confound; C has no reveal scores.

## Revisit triggers
- Pilot spread>=2 fires widely, or pilot P mean re-projects over $150 -> owner scope call before grid (bar-b cost premise threatened).
- #185 P verdict lands -> then decide the 0057 plateau cut-vs-keep.

## Act (post-ship — 2026-07-14)
- [outcome] classifier [checkable] verified — 20.1% family disagreement excluded + recorded; TESTED deltas cleared with margin (Phase-0 SUPPORTED, bare arm only).
- [outcome] "dual costs <$1" premise violated: $16.82 notional.
- [outcome] #185 H1 FALSIFIED judge-robust (bar c spread 0.281 vs 0.063 — mostly a decider capture defect; poker README correction); pre-grid triggers never fired — violated.
- [pivot] "#185 verdict lands" fired -> ADR 0062.
