---
id: 0096
title: "Truth-in-labeling round 2: every capability claim names the path that implements it"
status: accepted
summary: "The refuted skill-bench claims are one class, not six errors: the README describes the VERDICT path's properties and the #172 study's arm design as properties of the whole harness. Fix is subtractive — delete the uniqueness claims (two beyond the audit's surface list), scope arm and prosecutor claims to the implementing path, correct ADR 0055 in place, land in PR #321."
---

# 0096 — capability claims name their path

- Date: 2026-07-29
- Owner: PM
- Panel: none spawned (ADR 0062) — two prior adversarial evaluations (grok-4.5 cross-family;
  sonnet in-family), both partial-negative, both tree-verified; surviving findings folded in.
- Context: `skill-bench/README.md:17` claims "arm design (bare / cost-matched / structured)" but
  `bench_skill.py:71-72` builds exactly with/without; the three-arm design is the #172 study's,
  fed to `bench_verdict.py` as data. `judging.md:73-77` and `cost-and-verdict.md:36-38` teach
  grade-then-prosecute for "each cell"; only `bench_verdict.py:52` prosecutes. One root cause:
  path properties stated as harness properties.

## Decision
1. Every capability claim names its path. README drops `cost-matched` from the arm list (the
   historical #172 table stays — it records a design really run); judging.md and
   cost-and-verdict.md scope grade-then-prosecute to the verdict path (wiring: ADR 0098).
2. Delete the uniqueness claims; do not re-date them. "All of them report aggregate pass rates
   only" is refuted (LangSmith order randomization; Inspect dollar limits + multi-provider
   judges; Braintrust cross-vendor judge routing) — a dated false universal is still false.
   Replace with named prior art + an honest-limits paragraph. Also delete `README.md:3` "The
   repo's unique asset" and `README.md:30` "no vendor sells this" (missed by the audit).
3. The manifest pair moves in ONE commit: `.claude-plugin/marketplace.json` and
   `skill-bench/.claude-plugin/plugin.json` hold a byte-identical description whose tail claims
   a layer "no commercial eval tool provides"; the clause goes. manifestDrift already guards
   divergence; no new gate.
4. ADR 0055 corrected IN PLACE (rationalize): its summary's "no vendor sells" and its Why's
   "No commercial eval tool offers..." — measured before commit (12 chars headroom).
5. Sim home: the MDE range reproduces closed-form via `benchstats.mde80`, so ADR 0095's
   "sim: issue #303" cite is deleted rather than a script committed; the script posts to #303
   for the issue's own evidence. No merged ADR leans on an issue comment.
6. No work owed on the 87-task figure — already inside a dated survey block.
7. Vehicle: finish in PR #321 — its HEAD already edited these lines; a follow-up PR buys a
   conflict, not a revert boundary (ADR 0056).

## Justification
Subtractive: every item deletes or scopes a claim; none builds machinery. The adopter's gain is
a claim they can check. Root-cause framing (path conflation) beats six point edits.

## Assumptions
- [contradiction] **WEAKEST — corpus budget is FATAL, not advisory** (182,380/200,000;
  adr-lint). Binding ceilings for this batch, decided here: 0096 <=5,000; 0097 <=4,500;
  0098 lite <=2,000; 0093 amendment <=1,500. Write to the ceiling, not the 8,000 margin.
- [verified] 2 arms not 3 (`bench_skill.py:71-72`); no prosecute in the skill path
  (`bench_skill.py:24-36`); manifest descriptions byte-identical.
- [checkable] 0095's closed-form MDE cite reproduces 0.24-0.37 at G=6 unaided — owner: gate;
  result: verified (via `benchstats.mde80`, t multipliers 3.49 at G=6, s 0.17-0.26).
- [unverifiable] the three vendor refutations hold at merge — REOPEN-IF a named vendor drops
  the capability -> re-date the honest-limits paragraph, never re-universalize.

## Rejected alternatives
- Follow-up PR — conflicts on lines PR #321 just edited; no revert boundary gained.
- Date-scoping the "aggregate pass rates only" universal — that was the prior fix and is the
  defect this record closes.
- Rewriting the historical #172 arm table — erasing evidence to fit a claim.
- A new ADR amending 0055 — the template forbids it; rationalize in place.

## Revisit triggers
- A uniqueness claim ships without survey date + checked set -> promote to a PR-template
  checklist item.
- A capability claim describes a path that does not implement it -> the fix was wording, not
  structure; reopen.
