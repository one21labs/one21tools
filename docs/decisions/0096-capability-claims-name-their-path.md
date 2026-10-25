---
id: 0096
title: "Truth-in-labeling round 2: every capability claim names the path that implements it"
status: accepted
summary: "The refuted skill-measure claims are one class: VERDICT-path properties and the #172 study's arm design stated as properties of the whole harness. Fix is subtractive — delete the uniqueness claims, scope arm and prosecutor claims to the implementing path, correct ADR 0055 in place."
---

# 0096 — capability claims name their path

- Date: 2026-07-29
- Owner: PM
- Panel: none (ADR 0062) — two prior adversarial evaluations (grok-4.5 cross-family; sonnet
  in-family), both tree-verified; surviving findings folded in.
- Context: `skill-measure/README.md` claimed "arm design (bare / cost-matched / structured)" but
  `bench_skill.py:71-72` builds exactly with/without; the three-arm design is the #172 study's, fed
  to `bench_verdict.py` as data. `judging.md` and `cost-and-verdict.md` taught grade-then-prosecute
  for "each cell"; only `bench_verdict.py:52` prosecutes. One root cause: path properties stated
  as harness properties.

## Decision
1. Every capability claim names its path. The README arm list drops `cost-matched` (the
   historical #172 table stays — it records a design really run); judging.md and
   cost-and-verdict.md scope grade-then-prosecute to the verdict path (wiring: ADR 0098).
2. Delete the uniqueness claims; never re-date them. "All of them report aggregate pass rates
   only" is refuted (LangSmith order randomization; Inspect dollar limits + multi-provider judges;
   Braintrust cross-vendor judge routing) — a dated false universal is still false. Replace with
   named prior art + an honest-limits paragraph. Same for "the repo's unique asset" and "no vendor
   sells this" in `README.md`.
3. The manifest pair (`.claude-plugin/marketplace.json`, `skill-measure/.claude-plugin/plugin.json`)
   drops the "no commercial eval tool provides" clause in ONE commit; manifestDrift already guards
   divergence, no new gate.
4. ADR 0055 corrected IN PLACE (rationalize) — its "no vendor sells" claims removed.
5. ADR 0095's MDE cite is the closed form via `benchstats.mde80`, not an issue comment; no sim
   script is committed. No merged ADR leans on an issue comment.
6. No work owed on the 87-task figure — already inside a dated survey block.

## Justification
Root-cause framing (path conflation) beats six point edits, and every item deletes or scopes a
claim rather than building machinery — the adopter gains a claim they can check.

## Assumptions
- [verified] 2 arms not 3 (`bench_skill.py:71-72`); no prosecute in the skill path
  (`bench_skill.py:24-36`); manifest descriptions byte-identical.
- [checkable] 0095's closed-form MDE reproduces 0.24-0.37 at G=6 — owner: gate; result: verified
  (`(t95(5)+t80(5))*se` = 3.49 x s/sqrt(6) for s 0.17-0.26).
- [unverifiable] the three vendor refutations hold — REOPEN-IF a named vendor drops the capability -> re-date the honest-limits paragraph, never re-universalize.

## Rejected alternatives
- Date-scoping the "aggregate pass rates only" universal — the prior fix, and the defect closed here.
- Rewriting the historical #172 arm table — erasing evidence to fit a claim.
- A new ADR amending 0055 — the template forbids it; rationalize in place.

## Revisit triggers
- A uniqueness claim ships without survey date + checked set -> promote to a PR-template
  checklist item.
- A capability claim describes a path that does not implement it -> the fix was wording, not
  structure; reopen.
