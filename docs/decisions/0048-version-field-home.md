---
id: 0048
title: "Version bumps batch off feature PRs via a forcing function, not new machinery"
status: superseded by 0075
tier: lite
summary: "marketplace.json version-field rebase collisions (9 touches across #122-#138) came from coupling a bump to each feature PR, not an SSoT defect — the scar that later justified deleting version fields entirely. Superseded by ADR 0075; the bump cadence it decided is a dead path."
---

# 0048 — version bumps batch off feature PRs, not new collision machinery

- Decision (dead path): a feature PR did not bump a plugin version; each bump was its own PR,
  filed as an issue at batch start and cleared by the `/retrospect` pre-PR checklist — a forcing
  function, not new collision machinery.
- Why: `marketplace.json` was the most-churned file across #122-#138 (9 touches; one plugin
  bumped five times in a day) — contention from coupling a bump to every feature PR, not a
  version-home defect (that was already single-homed).
- Rejected: a merge-time bump bot/gate/lock, and a per-plugin `plugin.json` split — both
  disproportionate machinery for a one-line rebase.
- Superseded: ADR 0075 deleted plugin version fields outright, mooting this cadence.
- Enforced: superseded — see `0075-no-plugin-version-fields.md`.
