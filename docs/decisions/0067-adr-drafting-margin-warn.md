---
id: 0067
title: "Advisory drafting-margin WARN on new full ADRs in adr-lint"
status: accepted
tier: lite
summary: "adr-lint prints an advisory WARN (never a failure) when a --new-adrs full ADR exceeds ADR_CHAR_MARGIN (5,000) — the margin that reserves ## Act room. Scoped to PR-added ADRs so the 22+ legacy near-cap ADRs stay quiet; lite ADRs exempt. Closes #174."
---

# 0067 — advisory drafting-margin WARN on new full ADRs

- Decision: `adr-lint.mjs` gains `marginWarnings()` — an advisory WARN, never an exit-code
  change, when a full ADR in the `--new-adrs` set (CI passes the PR's added ADR files, ADR
  0051 plumbing) exceeds `ADR_CHAR_MARGIN` (5,000, new constant in `char-budget.mjs`). Lite
  ADRs are exempt (own cap, no Act machinery); the legacy corpus is never swept.
- Why: the template's margin prose is routinely ignored — 22+ ADRs sit at 5,900-6,000 with no
  `## Act` room left, and a PM agent drafted to 5,984 with the margin instruction in its own
  prompt — so the rule needs a mechanical rung; WARN-not-block because near-cap drafting can
  be rational cap-filling and the hard cap already gates, and new-ADRs-only scoping is what
  keeps a corpus-wide sweep from training everyone to ignore 22 permanent warnings.
- Enforced: `marginWarnings()` in `adr-lint.mjs` (wired to CI's `--new-adrs` step), decision
  logic pinned by four cases in `adr-lint.test.mjs`; spec note in adr-lint.md check 7.
