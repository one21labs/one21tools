---
id: 0051
title: "The PR is the decision-batching unit; cite-connectivity is an advisory WARN"
status: accepted
summary: "A PR ships one deliberately grouped work package of new ADRs — batching is declared by the PR itself, not inferred from cites. adr-lint --new-adrs reports cite-unconnected members as an advisory WARN (never a failure) so an accidental grab-bag is visible at review. Dangling-cite stays strict; revise-in-place unchanged."
---

# 0051 — the PR is the decision-batching unit

- Date: 2026-07-12; amended 2026-07-15 (owner directive: work packages ship as single PRs;
  cite-connectivity demoted from blocking gate to advisory)
- Owner: PM
- Panel: advisor evidence + options argued on issue #171; PM accepted. Amendment: owner call,
  no panel (ADR 0062 two-stage routing).
- Context: issue #154. The template's one-ADR-per-PR rule collides with the dangling-cite guard
  (adr-lint.md check 4): mutually-citing ADRs cannot ship in separate PRs. PR #151 shipped
  0047-0050 as one entangled set, the better for reviewing together. The amendment's trigger:
  cite-connectivity as a BLOCKING bar forced work package 1 (five deliberately-batched but
  cite-independent decisions, 0064-0068) into five PRs — five CI cycles, two merge-skew
  rebases, five retrospectives for one planned deliberation. Cohesion is a planning judgment;
  a cite graph can only proxy it, with exactly that false negative.

## Decision
1. **The PR is the batching unit.** One PR carries a single new ADR or a whole work package:
   decisions grouped at planning time, listed in the PR body, judged at review. No separate
   work-package entity is required. Splits follow ADR 0056's criteria (clean revert boundary,
   keep main green) plus spend gates. Operational wording lives in adr-template.md.
2. **Cite-connectivity is an advisory WARN.** `adr-lint --new-adrs` reports members outside
   the largest connected component (edge = either record cites the other) as
   `WARN (advisory, ADR 0051)` — never a failure. The WARN makes an ACCIDENTAL grab-bag
   visible at review; it does not judge cohesion. Precedent fixture both ways, pinned in
   adr-lint.test.mjs: 0047-0050 (entangled, quiet) and 0064-0068 (work package, warns, passes).
3. **The dangling-cite guard stays strict.** Corpus integrity is mechanical, not advisory:
   mutually-citing records still MUST ship together or the guard fails whichever lands alone.
4. **Fail-open plumbing unchanged.** Flag absent, empty, or a single new ADR = nothing
   reported; push-to-main, consumer checkouts, and local runs untouched.
5. **Revise-in-place is unchanged** — a still-unmerged ADR gets edited, never accompanied by a
   sibling written to overrule it.

## Justification
The gate's real job splits in two: corpus integrity (mechanical — stays blocking via
dangling-cite) and batching cohesion (judgment — moved upstream to planning, where the work
package is decided, and downstream to review, where the owner merges). CI keeps what it can
verify; the WARN keeps machinery-not-prose visibility (the original prose-loses lesson)
without the false-negative ceremony the blocking bar imposed on WP1.

## Assumptions
- [checkable] Both precedent shapes hold: 0047-0050 is quiet and 0064-0068 warns-but-passes —
  owner: adr-lint.test.mjs decision-set cases; result: verified in the amending change.
- [checkable] Fail-open is real: absent/empty `--new-adrs` and a singleton report nothing —
  owner: adr-lint.test.mjs; result: verified.
- [unverifiable] Review suffices to catch a genuine grab-bag once warned — REOPEN-IF a merged
  PR is found to have batched unrelated decisions that reviewing the WARN should have split;
  restore the blocking bar scoped to undeclared sets.

## Rejected alternatives
- **Relax the dangling-cite guard for cross-PR forward cites** — trades a working mechanized
  guard for coordination prose; an unmerged forward cite is permanent corpus damage.
- **A work-package entity (tracking issue / frontmatter field) as the connectivity edge** —
  a second artifact restating what the PR body already declares; ceremony without new
  information for a solo-owner repo.
- **Keep blocking, allow token bridge-cites** — pushes authors to game the gate; the original
  ADR's own REOPEN-IF named that failure.
- **Delete the check entirely** — loses the accidental-grab-bag signal the WARN keeps for free.

## Revisit triggers
- The [unverifiable] above fires -> restore blocking for undeclared multi-ADR sets.
- The CI diff wiring proves brittle (shallow-fetch or rename misses) -> move new-file
  detection into the lint itself or adopt a merge queue (the open #164 finding-2 question).
