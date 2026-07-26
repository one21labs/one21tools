---
id: 0090
title: "Retroactive record: semantic cite-ownership gate (check-cite-ownership.mjs)"
status: accepted
summary: "Records the gate CLAUDE.md required before build and didn't get: TERMS is a scar-backed list of exactly two, ownership keyed on uncredited-occurrence within tuned asymmetric windows (60 fwd / 25 back / 30 bind, measured), rung 4 FAIL under ADR 0047. Names the live limitation: a term with two legitimate owners for two concepts (append-only: ADR 0019 vs 0041) leaves the gate silent on a wrong-concept cite naming either owner."
---

# 0090 — semantic cite-ownership gate, written after the fact

- Date: 2026-07-26
- Owner: PM
- Panel: none — retroactive record of code already merged into this PR (CLAUDE.md's routine-call path, direct PM record). The judgment was already made by the builder; this catches the record up, doesn't re-decide.
- Context: `scripts/check-cite-ownership.mjs` shipped (commits 14ba12d/90095e6, #277) as a blocking CI gate (`gates.yml:63-64`) with no ADR — violates CLAUDE.md "a judgment call gets DECIDED and recorded... before it's built." Flagged 4x by advisory review on open PR #288, confirmed at session-close retrospect. Sibling `check-relocated-paths.mjs` in the same PR got a full panel record (ADR 0089) — the asymmetry is what the reviewer named.

## Decision
1. **TERMS stays scar-backed, exactly two** (`check-cite-ownership.mjs:34`): `"append-only"`, `"eval-clustered"`. Not auto-derived: no syntactic marker separates a load-bearing doctrine term from ordinary repeated prose — frequency-derivation gates everything or nothing. Not vacuous: each entry traces to a dated real mis-cite (below); `TERMS.length >= 2` is asserted as a floor, not a target (`check-cite-ownership.test.mjs:88-91`). **Growth rule: a third term is added only on its own recorded mis-cite** — same bar as the first two, never speculative.
2. **Ownership is occurrence-based, not mention-based.** An ADR owns a term iff >=1 occurrence is uncredited to a different ADR within window (`ownsTerm`, `check-cite-ownership.mjs:61-77`). "Appears at all" was insufficient: ADR 0025 uses "eval-clustered" 3x (`0025:5,13,16`) and credits ADR 0019 every time (0019 states it, `0019:5`) — presence-only would wrongly pass 0025 as an owner it explicitly disclaims.
3. **Windows are measured, the most contestable numbers.** `CREDIT_WINDOW=60` fwd: 40 misclassifies 0025's third occurrence (credit lands ~40+ chars out, `0025:16`); 80 classifies identically to 60, so 60 is the smallest window separating all six real pairs (`check-cite-ownership.mjs:38-41`, tested `test.mjs:132-135`). `CREDIT_WINDOW_BEFORE=25`, deliberately tighter: a symmetric 60 backward let a prior sentence's cite bleed forward and disclaim a term the record then claims itself (`.mjs:43-47`). `BIND_WINDOW=30`: nearest-cite binding alone measured 20% precision; preferring a FOLLOWING cite over nearer-preceding reached 100% on corpus — forced by the false positive at `0024-tool-cost-justification-loop.md:30` ("hermetic executor (ADR 0023) + eval-clustered CI (ADR 0019)"), asserted `test.mjs:64-68`.
4. **Known limitation, stated honestly: one term, two legitimate owners, is inexpressible.** "append-only" is ADR 0019's for result-snapshot JSONL format (`0019:5`) AND ADR 0041's for frozen dated dirs (`0041:19,22,27`). `ownsFn` is per-ADR not corpus-unique, so BOTH own it — the gate is silent whenever EITHER is cited, letting a wrong-concept cite pass. Hit live: `0036-routing-escalation-verdict.md:42` and `0037-parallel-run-evidence-home.md:11,17` cite ADR 0019 for "append-only" — correct under 0019's snapshot concept, but a reviewer reading "append-only" as the frozen-dir concept called them wrong. Fix applied was NOT to the gate — naming the CONCEPT in citing prose (0036:42 now "append-only result snapshot (ADR 0019)"; 0037:17 "the append-only result-snapshot rule (ADR 0019)"). The one-owner model can't resolve this class; accepted as a named residue, not silently patched.
5. **Rung 4, FAIL, under ADR 0047.** Cited scar: six real mis-cites in one session — `benchmarks/README.md` x2 + `skill-bench/skills/bench/SKILL.md:76` + `skill-bench/templates/grid.py:5` + `validate.py:35` + `validate_test.py:295` (all fixed, commits `1b9fabf`/`e9ebbb1`) — plus four the gate's own tuning then surfaced (ADR 0024 false positive, ADR 0070's `(ADR 0026/0041)` binding case, ADR 0036/0037's two-owner case). Economics: CI-only text check, no runtime cost. FAIL not WARN under 0047 precondition (ii) (WARN = undecidable intent): whether a cited ADR's text credits the term elsewhere is a mechanical string fact, not intent — same class as sibling 0089(c)'s FAIL. Precondition (i) (partial predicate ships its residue recorded): satisfied by decision 4 — the two-owner gap is named, not hidden.

## Justification
The gate is real, tested (21 cases, `check-cite-ownership.test.mjs`), already caught real corpus mistakes pre-merge — rebuilding isn't in question. Missing was the record CLAUDE.md requires before any judgment call ships: TERMS scope, the ownership predicate, three tuned constants are each contestable calls a future editor would otherwise re-derive from source comments alone, with no record of rejected values (40, 80, symmetric-60) or the knowingly-accepted limitation. Writing it now costs one PM pass; not writing it risks a future edit reopening the ADR 0025 misclassification the tuning already fixed.

## Assumptions
- [verified] TERMS = exactly two, scar-backed, growth-gated — `check-cite-ownership.mjs:34`, `test.mjs:88-91`.
- [verified] the six pre-gate mis-cites existed and are now corrected — `git show 1b9fabf --stat`, `e9ebbb1 --stat`; current text confirmed at each cited file:line, all now naming ADR 0041/0019.
- [verified] the four post-gate cases (0024/0070/0036/0037) are each asserted by a named test (`test.mjs:48-68`) or resolved in corpus prose (0036:42, 0037:17).
- [checkable] `node --test scripts/check-cite-ownership.test.mjs` passes — result: verified, 22/22 green (run 2026-07-26).
- [contradiction] this gate shipped without the ADR CLAUDE.md's PDCA-trigger rule requires before build — this record is the fix; the code needs no further change, only its record was missing.
- [unverifiable] a third scar-backed term will eventually surface, exercising the growth rule — REOPEN-IF a mis-cite outside current TERMS is found and not folded into decision 1 the same PR.

## Rejected alternatives
- Auto-derive TERMS from corpus frequency — no syntactic signal separates doctrine terms from prose; gates everything or nothing.
- One global term->owner map — can't express the real 0019/0041 append-only split (decision 4); forces an arbitrary tie-break that itself false-fires.
- WARN instead of FAIL — the predicate judges a mechanical text fact, not intent; 0047(ii)'s carve-out doesn't apply.

## Revisit triggers
- A term earns a third TERMS entry only via its own recorded mis-cite (decision 1) — absent that, TERMS stays at two.
- A THIRD concept collides on an existing term -> the per-ADR ownership model needs a concept-tag extension, not just prose discipline.
- The two-owner residue (decision 4) recurs on a DIFFERENT term pair -> promote from "name the concept in prose" to a structural fix (e.g. a `term:concept` key) rather than repeating the patch per incident.
