---
id: 0088
title: "adr-lint drift rungs: indexed constants match char-budget.mjs; discharged ADRs cannot stay proposed"
status: accepted
tier: lite
summary: "#254 (recorded misses, PR #251; #236 direction 2): (1) an .md line outside docs/decisions/ naming a char-budget.mjs constant beside a number must show its current value; (2) an ADR clause recording another ADR discharged fails while that ADR is still proposed."
---

# 0088 — drift lints: indexed constants + stale proposed status

- Decision: two adr-lint checks (#254): (1) docIndexDrift — an .md line outside docs/decisions/
  backtick-naming a char-budget.mjs scalar (or `DOC_BUDGETS` plus a key's filename) AND
  containing a 3+-digit number must include the constant's value (presence-only); (2) stale
  discharge — in a `;`-split clause containing "discharg", every cited existing ADR id still
  proposed fails.
- Why: recorded misses: doc-budgets.md indexed caps contradicting its named SSoT — invisible
  to check-restatement (prose, not numbers); ADR 0057 sat proposed 5 days after ADR 0062
  recorded its loop resolved. Measured first: docs/decisions/ is excluded from (1) — records
  hold as-of-decision numbers (ADR 0009); (2)'s clause split dodges the one
  historical near-miss (0057:28 cites then-proposed ADR 0055 beside a clause resolving
  ADR 0052).
- Enforced: `docIndexDrift()` + the discharge check in `lint()`,
  `pdca-workflow/scripts/adr-lint.mjs`; paired cases in `adr-lint.test.mjs` (required CI).
