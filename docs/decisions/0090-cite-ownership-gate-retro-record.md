---
id: 0090
title: "Retroactive record: semantic cite-ownership gate (check-cite-ownership.mjs)"
status: accepted
summary: "Record for check-cite-ownership.mjs (a blocking gate that shipped without an ADR): scar-backed TERMS, occurrence-based ownership, measured windows, and the named two-owner limitation."
---

# 0090 — semantic cite-ownership gate

- Date: 2026-07-26
- Owner: PM
- Context: `check-cite-ownership.mjs` shipped as a blocking gate with no ADR; this records the
  judgment without re-deciding it.

## Decision
1-3. **Scar-backed TERMS, occurrence-based ownership, measured windows** — each rule with its measured and rejected values lives in `scripts/check-cite-ownership.mjs` (header, `TERMS`, the window constants, `scanLine`).
4. **Known limitation: one term, two legitimate owners, is inexpressible.** "append-only" is ADR 0019's (result-snapshot JSONL) and ADR 0041's (frozen dated dirs); ownership is per-ADR, so the gate is silent whenever EITHER is cited, even for the wrong concept. Fix such cites in the CITING PROSE (name the concept), not the gate; accepted residue.
5. **Rung 4, FAIL, under ADR 0047.** Scar: six real mis-cites in one session plus four the gate's tuning surfaced (ADR 0024, 0070, 0036, 0037). FAIL not WARN: whether a cited ADR credits a term elsewhere is a mechanical string fact (ADR 0047 precondition ii). Precondition (i) is met by decision 4.

## Why
TERMS scope, the ownership predicate, and three tuned constants are each a contestable call a future editor would otherwise re-derive from source comments, with no record of rejected values or the accepted limitation.

## Assumptions
- [verified] TERMS = exactly two, growth-gated (`check-cite-ownership.mjs:37`); the six pre-gate mis-cites are corrected; `node --test scripts/check-cite-ownership.test.mjs` passes (22/22, 2026-07-26).
- [unverifiable] a third scar-backed term will eventually surface, exercising the growth rule — REOPEN-IF a mis-cite outside current TERMS is found and not folded into decision 1 the same PR.

## Rejected alternatives
- Auto-derive TERMS from corpus frequency — no syntactic signal separates doctrine terms from prose.
- One global term->owner map — can't express the 0019/0041 append-only split; any tie-break false-fires.
- WARN instead of FAIL — the predicate judges a mechanical text fact, not intent.

## Revisit triggers
- A THIRD concept collides on an existing term -> a concept-tag extension, not just prose discipline.
- The two-owner residue recurs on a DIFFERENT term pair -> a structural fix rather than the prose patch.
