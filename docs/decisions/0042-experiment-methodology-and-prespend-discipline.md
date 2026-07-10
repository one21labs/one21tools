---
id: 0042
title: "Paid experiments inherit verdict methodology and pre-spend discipline"
status: accepted
summary: "Three pre-run discipline rules (extend ADR 0024/0025) house in a NEW sibling reference skills/building-skills/references/pre-registration.md — empirical-evals.md (205-char headroom) takes only a pointer (ADR 0031 split-don't-cram): a pre-reg cites the settled verdict methodology instead of restating a superseded metric (#107); a cost-pilot (2-3 cells of the priciest arm) runs before any grid, stopping if a pre-registered gate is already decidable (#105); a size-gated prior-art pass precedes designing a paid experiment (#105)."
---

# 0042 — Paid experiments inherit verdict methodology and pre-spend discipline

- Date: 2026-07-10
- Owner: PM
- Panel: lean-process-engineer, process-economist, session-operator.
- Context: Paid experiments don't inherit settled methodology or pre-spend discipline. #107: pre-regs are free-form issue comments; #41's pre-reg named binary pass-rate AFTER ADR 0025 established fraction-met, and it floored 2/96 (third time). #105: two sessions spent executor budget on tiered orchestration whose DO-NOT-ADOPT outcome was predictable from known cascade economics; the cost gate was decidable after ~5 cells (~$0.60) but 216 ran (~90% saveable). Both land in empirical-evals.md (11,795/12,000 chars, 205 headroom — measured 2026-07-10 after PR #124's +21).

## Decision
The three rules do NOT fit empirical-evals.md's 205-char headroom, so (ADR 0031 split-don't-cram precedent) they house in a NEW sibling reference `skills/building-skills/references/pre-registration.md`; empirical-evals.md's "Authoring evals" section gains only a one-line pointer to it (a pointer is ~150 chars, fits 205). The new file ships with building-skills per ADR 0038; extends ADR 0024/0025:
1. **Pre-reg inherits methodology** (#107): a pre-registration CITES empirical-evals.md's verdict methodology (fraction-met headline, binary secondary, clustered-CI unit, cost accounting) instead of restating; it does not name a metric the ADRs already superseded.
2. **Cost-pilot before any grid** (#105): run 2-3 cells of the most expensive arm first; if a pre-registered gate is already decidable, stop and record. Unconditional (reorder, not new spend).
3. **Prior-art pass before designing a paid experiment** (#105): is the answer already known, and in what parameter regime? Test the OPEN regime. Size-gated — required only above a non-trivial spend threshold, not on small pilots.

## Justification
All three are experiment methodology that SHIPS with building-skills (ADR 0038) and inherit at the same surface (pre-run design + pre-reg), so one new home + one pointer. They form a coherent new sub-topic (pre-run discipline), so a sibling file is cleaner than surgically extracting an unrelated section from a near-full empirical-evals.md — and it keeps the near-full file at a pointer, not a cram. Cost-pilot is the highest-value (~90% executor spend saveable, ~$0.60 vs the full grid) and unconditional; prior-art is size-gated because mandating it on trivial pilots is gold-plate. Pre-reg-cites-methodology kills the recurring binary-floor fishing-accusation vector by reference, not restatement.

## Assumptions
- [verified] empirical-evals.md is 11,795/12,000 (205 headroom) — char count 2026-07-10 post PR #124; the three rules exceed 205, so they house in a new sibling file and empirical-evals.md takes only a ~150-char pointer.
- [verified] the append-only methodology home + fraction-met/binary rules live in empirical-evals.md (:155-162, verdict/snapshot sections) and ADR 0025 — read 2026-07-10.
- [checkable] after the edit empirical-evals.md stays ≤ 12,000 (the pointer is ~150 < 205) and the new pre-registration.md passes validate.py (references cap 12,000, no emoji) — owner: verifier at implementation.
- [unverifiable] a prior-art pass would have reframed the #41 experiment toward the routing/triage regime literature says can pay — REOPEN-IF a size-gated prior-art pass is skipped and a later paid experiment re-tests a settled regime.

## Rejected alternatives
- Do nothing beyond ADR 0025 (#107 honest option) — the floor recurred a third time; the fallback works but the fishing-accusation cost recurs each time.
- Mandate prior-art on every experiment — gold-plate on trivial pilots.
- Cram the three rules into empirical-evals.md's 205 headroom — cap breach; ADR 0031 says split, not cram.
- Surgically extract an existing empirical-evals.md section to free room — the three rules are a distinct new sub-topic, so a coherent sibling file beats fragmenting an unrelated section.

## Revisit triggers
- A pre-reg again names a superseded metric → the cite isn't binding; template the pre-reg comment itself.
- A grid again runs past a decidable cost gate → cost-pilot needs a hard stop (a gate script).

## Act (post-ship — 2026-07-10)
- [outcome] pre-registration.md ships with building-skills; empirical-evals.md took only the pointer (11,911/12,000 post-edit) — verified (PR #128).
- [process] red-team O6 was right that the rules could never fit the headroom; the sibling-file split was decided pre-build, not ad hoc.
