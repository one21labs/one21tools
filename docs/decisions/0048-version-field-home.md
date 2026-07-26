---
id: 0048
title: "Version bumps batch off feature PRs via a forcing function, not new machinery"
status: superseded by 0075
tier: lite
summary: "marketplace.json version-field rebase collisions (9 touches across #122-#138) came from coupling a bump to each feature PR, not an SSoT defect. Fix: feature PRs don't bump; each plugin's bump is its own PR, triggered by the /retrospect pre-PR checklist and tracked by an issue. Superseded by ADR 0075, which deleted plugin version fields outright."
---

# 0048 — version bumps batch off feature PRs, not new collision machinery

- Decision: a feature PR does not bump a plugin version; each plugin's bump is its own
  dedicated PR via the version writer. Forcing function: the pending bump is filed as a GitHub
  issue at batch start, cleared by the `/retrospect` pre-PR checklist — replacing the per-PR
  churn signal this removed.
- Why: `marketplace.json` was the most-churned file across #122-#138 (9 touches; one plugin
  bumped five times in a day) — contention from coupling a bump to every feature PR, not a
  version-home defect (that was already single-homed).
- Rejected: a merge-time bump bot/gate/lock — disproportionate machinery for a one-line
  rebase. A per-plugin `plugin.json` split as a collision fix — disproportionate, fixes only
  the cross-plugin case.
- Superseded: ADR 0075 deleted all plugin version fields outright (updates key on git content),
  mooting this cadence and its writer.
- Enforced: superseded — see `0075-no-plugin-version-fields.md`.
