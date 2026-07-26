---
id: 0090
title: "Retroactive record: semantic cite-ownership gate (check-cite-ownership.mjs)"
status: accepted
summary: "Records the gate CLAUDE.md required before build and didn't get: TERMS is a scar-backed list of exactly two, ownership keyed on uncredited-occurrence within tuned asymmetric windows (60 fwd / 25 back / 30 bind, measured), rung 4 FAIL under ADR 0047. Names the live limitation: a term with two legitimate owners for two concepts (append-only: ADR 0019 vs 0041) leaves the gate silent on a wrong-concept cite naming either owner."
---

# 0090 — semantic cite-ownership gate, written after the fact

- Date: 2026-07-26
- Owner: PM
- Context: `scripts/check-cite-ownership.mjs` shipped (#277) as a blocking CI gate with no ADR — a CLAUDE.md violation flagged on open PR #288 and confirmed at retrospect. Retroactive record of code already merged; the judgment isn't re-decided, only caught up.

## Decision
1. **TERMS stays scar-backed, exactly two** (`check-cite-ownership.mjs:34`): `"append-only"`, `"eval-clustered"`. No syntactic marker separates a doctrine term from ordinary prose, so growth is per-scar: a third entry is added only on its own recorded mis-cite (`TERMS.length >= 2` is a floor, not a target).
2. **Ownership is occurrence-based, not mention-based.** An ADR owns a term iff >=1 occurrence is uncredited to a different ADR within window (`ownsTerm`). Presence-only would wrongly certify a record that names a term while explicitly crediting a different one every time it appears — the gap this closed.
3. **Windows are measured, the most contestable numbers.** `CREDIT_WINDOW=60` forward: 40 misclassifies a real corpus case where a credit lands ~40+ chars out; 80 classifies identically, so 60 is the smallest window separating every real pair. `CREDIT_WINDOW_BEFORE=25`, deliberately tighter: a symmetric 60 backward let a prior sentence's cite bleed forward and wrongly disclaim a term the record then claims on its own account. `BIND_WINDOW=30`: nearest-cite binding alone measured 20% precision on the corpus; preferring a FOLLOWING cite over a nearer-preceding one reached 100% — forced by a false positive at ADR 0024:30 ("hermetic executor (ADR 0023) + eval-clustered CI (ADR 0019)").
4. **Known limitation: one term, two legitimate owners, is inexpressible.** "append-only" is both ADR 0019's (result-snapshot JSONL format) and ADR 0041's (frozen dated dirs). `ownsFn` is per-ADR, not corpus-unique, so both own it — the gate is silent whenever EITHER is cited, even for the wrong concept. Hit live: ADR 0036/0037 cite ADR 0019 for "append-only", correct under 0019's concept but ambiguous against 0041's — fixed in the CITING PROSE (name the concept), not the gate; accepted as a named residue.
5. **Rung 4, FAIL, under ADR 0047.** Cited scar: six real mis-cites in one session (benchmarks/README.md, skill-bench's SKILL.md, grid.py, validate.py, validate_test.py — all fixed) plus four the gate's own tuning then surfaced (ADR 0024, 0070, 0036, 0037). FAIL not WARN: whether a cited ADR's text credits a term elsewhere is a mechanical string fact, not undecidable intent (ADR 0047 precondition ii). Precondition (i) is satisfied by decision 4 — the two-owner gap is named, not hidden.

## Why
The gate is real, tested (21 cases), and already caught real corpus mistakes pre-merge. Missing was the record: TERMS scope, the ownership predicate, and three tuned constants are each a contestable call a future editor would otherwise re-derive from source comments alone, with no record of rejected values or the accepted limitation.

## Assumptions
- [verified] TERMS = exactly two, scar-backed, growth-gated (`check-cite-ownership.mjs:34`, `test.mjs:88-91`); the six pre-gate mis-cites are corrected; `node --test scripts/check-cite-ownership.test.mjs` passes (22/22, run 2026-07-26).
- [contradiction] this gate shipped without the ADR CLAUDE.md's PDCA-trigger rule requires before build — this record is the fix; the code needs no further change.
- [unverifiable] a third scar-backed term will eventually surface, exercising the growth rule — REOPEN-IF a mis-cite outside current TERMS is found and not folded into decision 1 the same PR.

## Rejected alternatives
- Auto-derive TERMS from corpus frequency — no syntactic signal separates doctrine terms from prose; gates everything or nothing.
- One global term->owner map — can't express the real 0019/0041 append-only split; forces an arbitrary tie-break that itself false-fires.
- WARN instead of FAIL — the predicate judges a mechanical text fact, not intent; 0047(ii)'s carve-out doesn't apply.

## Revisit triggers
- A term earns a third TERMS entry only via its own recorded mis-cite — absent that, TERMS stays at two.
- A THIRD concept collides on an existing term -> the per-ADR ownership model needs a concept-tag extension, not just prose discipline.
- The two-owner residue recurs on a DIFFERENT term pair -> promote from "name the concept in prose" to a structural fix rather than repeating the patch.
