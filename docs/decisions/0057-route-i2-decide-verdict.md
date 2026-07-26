---
id: 0057
title: "Route the I2 /decide verdict: measured loop first, dual-judge headline, claim/routing split"
status: accepted
summary: "Discharges ADR 0052's C~B trigger. All panel-composition change (incl. cut) goes through #180's arm-D loop; no candidate edit ships on assertion. Any v2/arm-D grid reports a dual-judge headline. The judge-sensitivity caveat ships now zero-spend; the trigger-text routing change is measurement-gated."
---

# 0057 — route the I2 /decide verdict

- Date: 2026-07-13
- Owner: PM
- Context: ADR 0052:40 fired (C~B -> route to its own /decide). I2 showed C-B +0.010 (CI straddling zero, opus NULL) at ~4x arm-A cost; a cross-family re-grade found C-B +0.125 with opus systematically more lenient — the null is judge-sensitive.

## Decision
1. **Route all panel-composition change through #180's arm-D measured loop; ship no candidate skill edit on assertion** (ADR 0024). Cut/lite-tier is also gated behind the loop, only after 3 valid iterations plateau.
2. **Any v2/arm-D grid reports a dual-judge headline (opus + cross-family), never opus-only** — surface divergence, don't average. Claim now (zero-spend): `pdca-workflow/README.md:27-29` states the null is judge-sensitive.
3. **Trigger scoping split.** Ship the claim caveat now; gate any trigger-text routing change diverting calls from the full panel (its one measured benefit is the RECORD) on an n=2-scenario, unverified-cause read. If pursued later, word it on checkable context-availability, never stakes.

## Justification
Route-to-loop: low risk (pre-registered bars + cost_gate) against the exp-4 independence edge. Shipping or cutting now both adopt a judge-sensitive, unproven read; dual-judge is near-free insurance against a wrong flagship headline.

## Assumptions
- [checkable] WEAKEST — the load-bearing lean rides on it: the +0.125 shift is genuine judge signal, not inflated by holding normalization on Claude. Direction is verified (opus one-directionally more lenient, 57/58 grades); magnitude is not, so the claim is kept to direction only. result: pending — named signal is the cross-family judge's owned reproduction.
- [unverifiable] context-thinness (not the specific synthetic traps) causes the thin-context cells' underperformance — n=2 scenarios, wide CI; why the routing edit is gated. REOPEN-IF a transcript diagnosis or arm-D confirms thinness is the driver.

## Rejected alternatives
- Ship candidates now — adopt-on-assertion (ADR 0024); cut/lite-tier the panel on the opus null — judge-sensitive; an opus-only headline — hides measured judge bias; a thin-context divert trigger now — trades the record away on an unverified-cause read.

## Revisit triggers
- Arm-D clears its four #180 bars -> adopt the shape; plateaus after 3 iterations -> record the null, decide cut vs keep.
- The cross-family re-grade shows the divergence was a normalization artifact -> soften the claim, make dual-judge advisory.
- A transcript diagnosis confirms context-thinness is causal -> ship the context-axis caveat.
