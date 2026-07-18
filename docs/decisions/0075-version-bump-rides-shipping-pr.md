---
id: 0075
title: "Version bumps ride the shipping PR (owner decision; supersedes 0048's cadence)"
status: accepted
tier: lite
summary: "A PR that ships plugin content bumps that plugin's version in the SAME PR via set-version.mjs — no dedicated version-bump PRs. Owner decision, 17-Jul-2026: \"I don't want version bump PRs. Just update the version and roll all related work into the main PR.\" Replaces ADR 0048's dedicated-PR cadence, whose /retrospect-checklist trigger was removed by the 16-Jul ceremony cut (its own revisit trigger then fired: PR #231 shipped a description change un-bumped)."
---

# 0075 — version bumps ride the shipping PR

- Decision: every PR that changes shipped plugin content includes that plugin's version bump
  (`set-version.mjs`, the one write path per ADR 0017). Dedicated bump PRs are retired.
- Why: ADR 0048's cadence depended on the per-PR /retrospect checklist as its forcing
  function; the ceremony cut (860c865) removed that trigger, and #231 promptly shipped
  content un-bumped — 0048's named reopen condition. Bumping in the shipping PR makes the
  content change itself the forcing function. The residual is 0048's original contention
  (parallel PRs colliding on the version line); accepted — each version is one JSON line and
  sync-before-spend (ADR 0043) resolves it.
- Enforced: CLAUDE.md Shipping section (the live policy home); ADR 0017 still owns the
  one-home write path; 0017:28's version-gates check stays the escalation if bumps rot.
