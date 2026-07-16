---
id: 0030
title: "PR body: Purpose / Changes / Testing / Deferred; retrospects are on-demand"
status: accepted
summary: "A PR body carries Purpose / Changes / Testing / Deferred. The per-PR retrospect mandate and its Retrospective: line are removed (owner rework 2026-07-16, the ceremony cut): /retrospect is an on-demand instrument, run when something felt wrong — the repo's own measurements found no per-PR quality edge, and the ritual's green line manufactured false assurance. check-pr-body keeps only the ADR 0054 title/Partial contradiction guard. Git history carries the original mandate."
---

# 0030 — PR body sections; retrospect on demand

Owner decision, recorded directly (2026-07-16). Enforced homes: `scripts/check-pr-body.mjs`
(ADR 0054 guard only), `.claude/hooks/pr-create-guard.sh` (disclosure + body-file + external
target), CLAUDE.md Shipping.

- [unverifiable] on-demand retrospects catch what the per-PR ritual caught — REOPEN-IF a
  defect class ships that a routine retrospect demonstrably used to surface (a measured
  recurrence, not a hunch).
