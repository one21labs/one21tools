---
id: 0039
title: "Route #93 authoring-time prevention rules to their shipped reference homes"
status: accepted
tier: lite
summary: "Adopt eight one-line authoring-time prevention rules from #93 (audit method + trigger cadence; search-before-state; ban expiring status prose; test-the-surface; root-cause handoff + issue-shape; JIT timing row; routing-bypass anti-pattern), each at its shipped reference home per ADR 0038. Reject item 9c (in-flight-kill economics) as gold-plate."
---

# 0039 — route #93 authoring-time prevention rules to shipped homes

- Decision: adopt eight rules, each at its shipped home (ADR 0038): corpus-scoped audit method,
  trigger-based not fixed-cadence, + root-cause handoff + one-issue-per-root-cause shape ->
  `waste-identification.md`; search-before-state + ban expiring status prose ->
  `ssot-enforcement.md`; test-the-surface -> `validation-rules.md`; a rule firing at an
  action-moment needs a hook not a JIT reference -> `jit-documentation.md` Decision Test; a
  CLAUDE.md deep-link bypassing a skill's routing is an anti-pattern -> `claude-md.md`.
  Rejected item 9c (in-flight-kill economics). One PR across 3 skills — one concern (shipped
  homes), not one-file-per-concern.
- Why: each rule is a verified-unhoused, one-line addition to a file that already ships (near-
  zero cost). Closes #93's Branch B gap (audit process ended at Categorize, no root-cause
  handoff) and the routing-bypass mechanism, in homes every consumer inherits.
- Rejected: a fixed audit cadence — overproduction between triggers. Repo-only homes (CLAUDE.md,
  ISSUE_TEMPLATE) — consumers don't inherit them. Item 9c — the issue's own text flags it as
  gold-plate.
- Reopen-if: an audit finds a waste class none of these rules addresses -> extend the taxonomy.
  The cadence proves mis-tuned (two audits find <3 or >20 items) -> retune it.
- Enforced: all eight rows shipped, verified under reference char caps (PR #132).
