---
id: 0060
title: "Budget edits get a prevent rung: PreToolUse guard denies over-cap edits before they land"
status: accepted
tier: lite
summary: "Owner-direct: the measure-first discipline (doc-budgets.md) gets a poka-yoke. A PreToolUse hook computes the projected post-edit size of any budgeted doc (caps imported live from char-budget.mjs) and DENIES an edit landing over cap, with the headroom math. Never traps a fix (shrinking always passes); fails open; 10-case test in CI."
---

# 0060 — budget-edit prevent rung

- Decision: `.claude/hooks/budget-edit-guard.sh` wired PreToolUse on Edit|Write, scoped to the
  budgeted classes (CLAUDE.md, ADRs incl. lite tier by resulting frontmatter, agent prompts,
  the pdca-init template). Ladder position (ADR 0047): PREVENT, above the existing post-edit
  lint and CI rungs, which stay (defense in depth; the hook fails open by design). Repo-local
  for now — promotion into the plugin is a consumer-facing call for a later /decide.
- Why: a prose-only budget discipline has no executable feedback — overruns surface only as
  edit-validate-trim rework after the fact; computing the verdict before the edit is the
  cheapest point in the ladder and makes the failure impossible rather than caught.
- Enforced: `test-budget-edit-guard.sh` (10 cases: deny + headroom math, shrink-always-allowed,
  lite tier, fail-open) in the gates.yml hook glob; check-gate-tests registers it.
