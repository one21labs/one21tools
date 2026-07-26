---
id: 0051
title: "The PR is the decision-batching unit; cite-connectivity is an advisory WARN"
status: accepted
tier: lite
summary: "A PR ships one deliberately grouped work package of new ADRs — batching is declared by the PR itself, not inferred from cites. adr-lint --new-adrs reports cite-unconnected members as an advisory WARN (never a failure) so an accidental grab-bag is visible at review. Dangling-cite stays strict; revise-in-place unchanged."
---

# 0051 — the PR is the decision-batching unit

- Date: 2026-07-12; amended 2026-07-15 (owner directive: work packages ship as single PRs;
  cite-connectivity demoted from blocking gate to advisory).
- Decision: the PR is the batching unit — one PR carries a single new ADR or a whole work
  package, listed in the PR body, judged at review; no separate work-package entity is required.
  `adr-lint --new-adrs` reports members outside the largest connected cite-component as
  `WARN (advisory)` — never a failure. The dangling-cite guard stays strict: mutually-citing
  records still MUST ship together. Revise-in-place unchanged.
- Why: the gate's real job splits in two — corpus integrity (mechanical, stays blocking) and
  batching cohesion (a planning judgment a cite graph can only proxy: the blocking bar forced a
  5-decision work package into 5 separate PRs and merge-skew rebases).
- Rejected: relax the dangling-cite guard for cross-PR forward cites (permanent corpus damage) —
  a tracking entity as the connectivity edge (restates the PR body) — delete the check entirely.
- Reopen-if: a merged PR is found to have batched unrelated decisions that reviewing the WARN
  should have split -> restore the blocking bar scoped to undeclared sets.
- Enforced: `pdca-workflow/scripts/adr-lint.mjs` (`--new-adrs` WARN), `adr-lint.test.mjs`
  (0047-0050 quiet, 0064-0068 warns-but-passes fixtures).
