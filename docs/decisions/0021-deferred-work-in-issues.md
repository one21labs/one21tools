---
id: 0021
title: "Deferred work lives in GitHub issues, not repo files"
status: accepted
tier: lite
summary: "Work-state tracks as GitHub issues, never repo to-do/handoff files. Amended (owner, 28-Jul-2026): an issue is the EXCEPTION, not the default — a finding is fixed in-session, discarded, or handed to the owner as a memo; only work someone must act on later earns an issue. Boundary: ADRs keep decision-state (revisit triggers never move); repo docs keep method/protocol."
---

# 0021 — deferred work lives in GitHub issues

- Decision: what tracks at all tracks as a GitHub issue, never a repo file. Amended (owner,
  28-Jul-2026): filing is the exception — a finding is fixed in-session, discarded, or handed
  to the owner as a memo; only work someone must act on later earns an issue. Full rule:
  `CLAUDE.md` "Shipping — PR".
- Why: a to-do file has no lifecycle and can only drift; and filing is free while closing is
  owner-only — default-to-issue grew a 20-issue self-audit backlog; the valve is the fix.
- Enforced: CLAUDE.md Shipping rule + owner review of PR Deferred sections; no tracked
  handoff/TODO doc remains in the repo.
