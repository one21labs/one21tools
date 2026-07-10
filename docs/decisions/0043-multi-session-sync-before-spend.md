---
id: 0043
title: "Sync-before-spend before executing an issue; claim when write-permission allows"
status: accepted
summary: "Repo-instance coordination in CLAUDE.md (extends the existing post-merge fetch+rebase rule): before executing an issue, git fetch origin main + re-read the issue and PRs referencing it, and repeat before the final push (mandatory); post a one-line in-progress claim comment when issue-write permission is available (conditional — no-ops when withheld). Prevents the parallel duplicate-spend that ran issue #30 twice (#106)."
---

# 0043 — Sync-before-spend before executing an issue; claim when write-permission allows

- Date: 2026-07-10
- Owner: PM
- Panel: process-economist, session-operator.
- Context: A dispatched session executed issue #30 in full (~$5-8 of nested claude -p) while main already carried the merged fix (PR #97 closed #30 concurrently); discovered only at end-of-session git fetch (#106). Nothing forces a working session to re-sync origin/main and re-read the target issue immediately before spending, or to leave a visible claim. This is repo-instance coordination (git + this repo's issues) — CLAUDE.md home, legitimately not shipped (ADR 0038).

## Decision
Add to CLAUDE.md's Shipping/PDCA section (extends the existing "fetch + rebase after any upstream PR merges" rule):
1. **Sync-before-spend** (mandatory): before executing an issue, `git fetch origin main` + re-read the issue and search PRs referencing it; repeat before the final push.
2. **Claim protocol** (conditional): when issue-write permission is available, post a one-line "in progress (session X)" comment at execution start; clear it on completion. NOT mandated — dispatch instructions sometimes withhold issue-write by design, so the claim silently no-ops there.

## Justification
Sync-before-spend is cheap prose against a realized $5-8 duplicate; it catches unclaimed collisions and naturally extends the rule already in CLAUDE.md. #106 labeled both mitigations weak (prose can be skipped) — prose is nonetheless the right surface NOW because the mechanized alternative (a shipped dispatch template with auto-fetch) does not exist to amend; the revisit names that mechanized replacement, and because the rule is unproven the revisit fires on the FIRST post-rule collision, not a third. The claim catches long-running collisions but is [unverifiable]-reliable (no-ops without write permission), so it's conditional, not mandatory. Both stay repo-instance (CLAUDE.md): they govern THIS repo's git/issue workflow; an installed consumer's coordination is their own (ADR 0038 — legitimately not a shipped rule).

## Assumptions
- [verified] CLAUDE.md's Shipping section already carries a post-merge fetch+rebase rule this extends (no new home) — read 2026-07-10.
- [checkable-doc] the sync rule doesn't duplicate an existing CLAUDE.md line — verified: the existing rule fires post-merge to rebase a live branch, not pre-spend for an issue's state; distinct trigger.
- [unverifiable] prose sync-before-spend actually gets followed under dispatch pressure — REOPEN-IF the FIRST duplicate-spend collision occurs after the rule ships (the rule is unproven; one failure is enough to mechanize).

## Rejected alternatives
- Claim protocol as mandatory — fails silently when issue-write is withheld; mandating an unenforceable step is theater.
- Mechanized dispatch auto-fetch now — no shipped dispatch template exists to amend (session-operator [unverifiable]); prose is the available surface until one does.
- Ship the rule in references/ — it's repo-instance git/issue workflow, not skill/plugin operation.

## Revisit triggers
- The first duplicate-spend collision after this rule ships → mechanize the sync (auto-fetch at dispatch), don't add more prose.
- A shipped dispatch/orchestration template appears → inline sync + claim as literal steps there.
