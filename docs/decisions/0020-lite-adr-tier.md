---
id: 0020
title: "Lite ADR tier for settled decisions — one home, mechanical boundary"
status: accepted
tier: lite
summary: "Small settled decisions record as tier: lite ADRs in docs/decisions/ (same dir, id sequence, catalog): Decision / Why / Rejected / Reopen-if / Enforced, capped by LITE_ADR_CHAR_BUDGET. Boundary (amended by ADR 0092): the discriminator is ASSUMPTION MACHINERY, not a live trigger — a lite record may carry a Reopen-if line; a tagged assumption bullet or an Assumptions section forces graduation to full."
---

# 0020 — lite ADR tier for settled decisions

- Decision: `tier: lite` frontmatter in `docs/decisions/` — same directory, id sequence, and
  skim catalog as full ADRs. Shape: Decision / Why / Rejected / Reopen-if / Enforced, under
  `LITE_ADR_CHAR_BUDGET`. **Boundary (amended by ADR 0092):** the discriminator is ASSUMPTION
  MACHINERY, not a live trigger. A lite record may carry a plain Reopen-if line — that alone no
  longer forces graduation. What forces full is reasoning that must survive for a later reader
  to resolve: a checkable/checkable-doc/contradiction/unverifiable-tagged assumption bullet, or
  an Assumptions section tracking them. adr-lint.mjs enforces this mechanically.
- Why: full ADRs must state a falsifiable criterion; "carries unresolved assumption machinery"
  partitions full from lite with zero new judgment, and the linter polices it. The pre-0092
  rule (any live trigger forces full) over-graduated: a Reopen-if is exactly the anti-churn
  field a settled call still needs.
- Rejected: a separate `decisions.md` — fragments the catalog. No tier at all — loses the
  browsable why; the bar becomes the fuzzy meta-decision. A CLAUDE.md changelog — always-loaded
  cost, drift-prone.
- Reopen-if: a lite record is re-litigated or graduates twice -> tighten it. The tier grows
  large but unread -> fold it.
- Enforced: `pdca-workflow/scripts/adr-lint.mjs` + `adr-lint.test.mjs`; caps in
  `char-budget.mjs`.
