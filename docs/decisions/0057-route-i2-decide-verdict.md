---
id: 0057
title: "Route the I2 /decide verdict: measured loop first, dual-judge headline, claim/routing split"
status: accepted
summary: "Discharges ADR 0052's C~B trigger. All panel-composition change (incl. cut) goes through #180's arm-D loop; no candidate edit ships on assertion. Any v2/arm-D grid reports a dual-judge headline. The judge-sensitivity caveat ships now zero-spend; the trigger-text routing change is measurement-gated."
---

# 0057 — route the I2 /decide verdict

- Date: 2026-07-13
- Owner: PM
- Panel: process-economist (assigned cut), session-operator (assigned amplify), lean-process-engineer (neutral). plugin-adopter skipped — panel-mechanism scope; the only adopter-facing piece is claim wording, governed by the #164-f3 claim-accuracy precedent.
- Context: ADR 0052:40 fired (C~B -> route to its own /decide, don't silently keep the claim). I2: C−B +0.010, CI [−0.177,+0.198], opus NULL (`benchmarks/2026-07-12-pdca-decide-outcome/README.md:124-134`); ~4x arm-A cost, ~0 rubric delta. Structure (README:138-149): exp-4 failure-anticipation is the panel's one edge (C 0.42 / A 0.25 / B 0.08 — independence, not tokens, is the active ingredient); exp-3 assumption-surfacing is shared headroom (0.17-0.33 all arms); S1/S4 thin-context −0.33 (2 scenarios). Cross-family re-grade (`skill-bench/scripts/lib/PROTOTYPE-i2-result.json`): C−B +0.125, opus 57/58 disagreements more lenient — the null is judge-sensitive.

## Decision
1. **Route ALL panel-composition change through #180's arm-D measured loop; ship no #179 candidate skill edit (mandatory premortem, assumption-hunt, evidence-weighing) on assertion.** ADR 0024 forbids adopt-on-assertion — the rule that killed tiered execution. Arm D IS the exp-4 independence mechanism prototyped (decider + independent probes), not a bypass. **Cut / lite-tier of the panel is ALSO gated behind the loop** — 0024's cut-is-fallback, only after 3 valid iterations plateau.
2. **Any v2/arm-D grid reports a DUAL-JUDGE headline (opus + cross-family), never opus-only;** surface divergence, don't average (ADR 0019's family-bias residual + 0055's diagnostic). Binds regardless of 0055's fate. Claim NOW (zero-spend, #164-f3): amend `pdca-workflow/README.md:27-29` — the null is JUDGE-SENSITIVE (a cross-family re-grade found opus systematically more lenient, moving the estimate toward weak-positive).
3. **Trigger scoping — SPLIT.** Ship now: the claim caveat only. GATE any trigger-text ROUTING change diverting calls from the full panel: `decide/SKILL.md:14-15` routes feedback here for the RECORD — the panel's one MEASURED benefit (process guarantees, README:28). A thin-context divert trades the record away for an unproven rubric-cost saving, on n=2 scenarios + an unverified cause — a design call for the loop, not docs-honesty. If pursued, word it on the checkable context-availability axis (repo/artifact present at Inherit, y/n), NEVER on stakes (S1/S4 are high-stakes — stakes-wording pattern-matches back into the underperforming case).

**Implementation (tech-lead, post-gate):** one-line `README.md:27-29` judge-sensitivity caveat (both estimates). No /decide skill or agent edit until arm-D clears its four #180 bars.

## Justification
Route-to-loop: risk low (0024's pre-registered bars + cost_gate) x value high — targets the exp-4 edge + exp-3 headroom. Ship-edits-now violates 0024 (a prompt-slot alone isn't poka-yoke — the assumption slot sat at 0.17-0.33); cut-now adopts a judge-sensitive null. Dual-judge is near-free (re-grade, no new generation) insurance against a wrong flagship headline. Splitting the trigger discharges honesty now while gating a behavioral change a subgroup read can't yet justify.

## Assumptions
- [verified] opus is one-directionally more lenient than the cross-family judge — `PROTOTYPE-i2-result.json`: 57 stricter / 1 looser of 58 grades, one-directional. Supports the claim + dual-judge headline.
- [checkable] WEAKEST — the load-bearing lean rides on it: the +0.125 magnitude / weak-positive shift is genuine judge signal, not inflated by holding normalization on Claude (ADR 0055's named residual). DIRECTION is verified above; the MAGNITUDE is not clean, so the claim wording is kept to DIRECTION. TEST is 0055's owned reproduction (re-grade cross-familying the normalizer). — owner: #180 pre-spend. result: pending — the gate cannot run new generation in-session; named signal is 0055's re-grade.
- [checkable-doc] no accepted ADR contradicts: discharges 0052:40; 0024 governs improve-before-cut; 0019/0025 own CI/metric; 0055 (proposed) owns the cross-family judge, referenced not re-decided. result: verified.
- [unverifiable] context-thinness (not the specific synthetic traps) causes S1/S4's −0.33 — n=2 scenarios, wide CI; this is WHY the routing edit is gated. REOPEN-IF a transcript diagnosis (0024) or arm-D confirms thinness is the driver.
- [unverifiable] arm-D's probes isolate independence vs merely adding tokens — #180 tests; REOPEN bounded by #180's four bars.

## Rejected alternatives
- Ship candidates 1-2 now — adopt-on-assertion (0024).
- Cut / lite-tier the panel now on the opus null — judge-sensitive; cut is 0024's fallback only after plateau.
- Opus-only headline for arm-D — hides measured judge bias on the flagship's only outcome evidence (exp-2's opus ceiling broke to C 0.83 vs B 0.54 under grok).
- Ship a thin-context divert trigger edit now (candidate 3/5) — trades the record away on an n=2 subgroup + unverified cause.

## Revisit triggers
- Arm-D clears its four #180 bars -> adopt the shape; edit /decide + agents + the claim sweep to the new measurements.
- Arm-D plateaus after 3 valid iterations (0024) -> record the null; decide cut vs keep-current-panel, process-guarantee value explicit.
- 0055's re-grade shows the divergence was a normalization artifact -> soften the judge-sensitivity claim; make dual-judge advisory.
- A transcript diagnosis confirms context-thinness is causal -> ship the context-axis routing caveat.
