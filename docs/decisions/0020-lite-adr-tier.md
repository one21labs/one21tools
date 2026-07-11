---
id: 0020
title: "Lite ADR tier for settled decisions — one home, mechanical boundary"
status: accepted
summary: "Small settled decisions record as `tier: lite` ADRs in docs/decisions/ — decision + why + where-enforced, <=1,500 chars, exempt from the criterion gate. The boundary is mechanical, derived from the existing falsifiability rule: a live REOPEN-IF / [unverifiable] / Revisit-triggers section means NOT settled, and adr-lint rejects it from the lite tier ('graduate to a full ADR'). Rejected: a separate decisions.md (second decision home, drifts from the catalog); no tier at all (loses why-history for mechanical calls). Cuts full-ADR ceremony for calls that don't warrant it, without fragmenting the corpus."
---

# 0020 — lite ADR tier for settled decisions

- Date: 2026-07-07
- Owner: PM
- Panel: owner-direct (owner raised ADR proliferation + authoring ceremony; picked lite-in-docs/decisions over a separate decisions.md and over no-tier when offered the trade-offs); gates (adr-lint decision-logic tests) ran as Check.
- Context: every recorded decision paid full-ADR ceremony (panel line, tagged assumptions, rejected alternatives, revisit triggers) even when the call was mechanical and already enforced by a test. The corpus grew a record per small call, and the alternative — not recording — loses the why. Needed: a cheaper record WITHOUT a second decision home or a fuzzy "is this ADR-worthy?" meta-decision.

## Decision
1. **`tier: lite` frontmatter in docs/decisions/** — same directory, id sequence, and skim catalog (one home preserved). Shape: Decision / Why / Enforced-at, <=1,500 chars (`LITE_ADR_CHAR_BUDGET`, char-budget.mjs).
2. **Mechanical boundary, lint-enforced** (adr-lint.mjs; cases in adr-lint.test.mjs): full boundary
   rule in `adr-template.md`'s "Lite tier" section — a live trigger means not settled, so the record
   must graduate. Lite records are exempt from the falsifiability gate (settled = nothing left to
   test) but still subject to id/frontmatter, version-agnostic, dangling-cite, and duplicate-id guards.
3. **Graduation is in-place**: a lite record that gains a trigger is rewritten as a full ADR, same id — tier is state, not history.
4. Authoring rules live once in adr-template.md's "Lite tier" section; the caps live once in char-budget.mjs.

## Justification
The boundary falls out of a rule the corpus already enforces — full ADRs MUST state a falsifiable criterion, so "has a live criterion/trigger" cleanly partitions full from lite with zero new judgment. Poka-yoke over convention: the linter, not reviewer memory, polices the tier (a lite record smuggling a trigger is rejected, not merely frowned at). Cost ~30 lines of tested lint logic + a template section; benefit: full ceremony reserved for contested calls, small calls keep their why.

## Assumptions
- [checkable] the tier boundary, lite budget, graduation message, and retained guards are covered by adr-lint.test.mjs — owner: gates (node --test); result: green (28 cases).
- [unverifiable] WEAKEST: authors route correctly between tiers in practice — REOPEN-IF a lite record's decision is later re-litigated or reopened twice (the tier hid a live trade-off), or the lite tier accumulates records nobody ever reads; then tighten the boundary or fold the tier.

## Rejected alternatives
- **Separate decisions.md** (the original proposal): a second decision home — fragments the catalog, drifts from adr-lint's guards, and needs its own linter + cap anyway; everything it buys, lite-in-place buys without the split.
- **No tier — raise the ADR bar**: settled calls live only in their enforcing test + commit message; loses the browsable why for mechanical decisions, and the bar itself becomes the fuzzy meta-decision.
- **A "Learned"/changelog section in CLAUDE.md**: always-loaded cost + exactly the drift-prone backstory log CLAUDE.md bans.

## Revisit triggers
- A lite record is re-litigated or graduates twice -> the boundary is hiding live trade-offs; tighten it.
- The lite tier grows large but unread -> fold it; the enforcing tests were the real record.
