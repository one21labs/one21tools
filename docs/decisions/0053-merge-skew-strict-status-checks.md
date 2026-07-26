---
id: 0053
title: "Merge-skew prevention: require branches up-to-date on the gates check"
status: accepted
tier: lite
summary: "Prevent the individually-green / combined-red merge-skew class by enabling branch protection 'Require branches to be up to date before merging' (strict status checks) on the required gates check — a strict re-run recomputes the full on-disk budget on the merged content. Reject merge queue (premature; 0051 parks it as the escalation) and accept-risk. Ships as one decision-set with ADR 0054 (sibling merge-time integrity failure)."
---

# 0053 — merge-skew prevention via strict status checks

- Decision: on the required `gates` check, enable BOTH "Require branches to be up to date before
  merging" AND "Do not allow bypassing the above settings." The second is load-bearing: branch
  protection does not bind admin/agent tokens unless bypass is disabled, and the scar's merges
  were admin-token merges. Strict mode locks the merge button until `gates` re-runs green
  against the current base.
- Why: PRs #162/#163 each passed `gates` individually, merged 7s apart, and their combined char
  growth broke main's budget — GitHub let the merge proceed against a stale base. adr-lint
  budgets the FULL on-disk file, so a strict re-run against the updated base recomputes the
  combined budget and catches exactly this class.
- Rejected: GitHub merge queue — premature, heavier machinery; no scar shows strict checks
  insufficient (0051 parks it as the escalation). Accept risk — the scar broke main.
- Reopen-if: strict re-run churn materially slows merge cadence -> adopt merge queue. A
  merge-skew breakage recurs despite strict mode -> widen a gate or escalate.
- Enforced: `.github/workflows/gates.yml` + the two GitHub branch-protection toggles
  (owner-flipped; tracked by an ADR-0021 deferred issue).
