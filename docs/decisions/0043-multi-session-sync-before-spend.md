---
id: 0043
title: "Sync-before-spend before executing an issue; claim when write-permission allows"
status: accepted
tier: lite
summary: "Repo-instance coordination rule added to CLAUDE.md's Shipping section (extends the existing post-merge fetch+rebase rule) — full rule text there. Prevents the parallel duplicate-spend that ran issue #30 twice (#106)."
---

# 0043 — sync-before-spend before executing an issue; claim when write-permission allows

- Decision: two rules added to CLAUDE.md's Shipping section (extends the existing post-merge fetch+rebase rule; full text there): (1) sync-before-spend, mandatory — `git fetch origin main` + re-read the target issue immediately before executing it; (2) a claim protocol (post an in-progress comment), conditional on issue-write permission being available, not mandated.
- Why: a dispatched session executed issue #30 in full (~$5-8 of nested spend) while `main` already carried the merged fix from a concurrent PR, discovered only at end-of-session sync (#106). Cheap prose against a realized duplicate-spend cost; the claim step is conditional because it no-ops silently without write permission, and mandating an unenforceable step would be theater.
- Rejected: claim protocol as mandatory (fails silently when issue-write is withheld); a mechanized dispatch auto-fetch now (no shipped dispatch template exists yet to amend); shipping the rule in `references/` (it's repo-instance git/issue workflow, not skill/plugin operation).
- Reopen-if: the first duplicate-spend collision occurs after this rule ships -> mechanize the sync (auto-fetch at dispatch) instead of adding more prose. A shipped dispatch/orchestration template appears -> inline sync + claim as literal steps there.
- Enforced: `CLAUDE.md` "Shipping — PR" ("Sync before spend").
