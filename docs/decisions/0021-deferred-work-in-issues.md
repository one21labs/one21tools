---
id: 0021
title: "Deferred work lives in GitHub issues, not repo files"
status: accepted
tier: lite
summary: "Work-state (deferred items, handoffs, pending tasks) tracks as GitHub issues — state with a lifecycle that closes when done; repo files never carry to-do lists or handoff docs. Boundary: issues own tasks; ADRs keep decision-state (revisit triggers never move); repo docs keep method/protocol. PR Deferred sections link the issues."
---

# 0021 — deferred work lives in GitHub issues

- Decision: deferred work tracks as GitHub issues, not repo files. Full rule + the issues/ADRs/
  repo-docs boundary: `CLAUDE.md` "Shipping — PR" ("Deferred = issues").
- Why: a to-do list in a file has no lifecycle and can only drift — an issue is open-or-closed
  and dies when done; a fresh session reads the open issues instead of hunting for a handoff.
- Enforced: CLAUDE.md Shipping rule + owner review of PR Deferred sections; adopted with the
  migration to issues #30-#34 and the handoff file's removal from the benchmark snapshot; no
  tracked handoff/TODO doc remains in the repo.
