---
id: 0050
title: "Plugin distribution: standalone plugins; dependencies only where content requires"
status: accepted
tier: lite
summary: "Every marketplace plugin installs standalone — no plugin declares a dependency to distribute behavior. pdca-workflow's hooks are dev tooling for adopting repos, not a product that travels with skills. A dependency arrow may exist only where one plugin's content cannot function without another's files — today that set is empty. The shared ./skills source stays."
---

# 0050 — standalone plugins; content-true dependencies only

- Decision: every marketplace plugin installs standalone — no plugin declares a `dependencies` field to distribute behavior. A dependency arrow may exist only where one plugin's content cannot function without another's files (today that set is empty). pdca-workflow's enforcement hooks are dev tooling for adopting repos, not a product that travels with skills; where they should fire (per-project vs session-wide) is undesigned. The shared `./skills` source stays — no per-plugin split.
- Why: judge the artifact as the person on the receiving end — a stranger installing one reference skill must not receive an opinionated process framework and session-wide guards they did not ask for. The skills carry no functional dependency on pdca-workflow.
- Rejected: an enforced pdca-workflow dependency on every plugin (this ADR's original decision) — rested on an owner-attributed directive the owner disavowed when asked; one monolith plugin — forces every skill's description into every consumer's context; a hooks-only carrier plugin — packages hooks before firing scope is designed.
- Reopen-if: the hooks-scope design lands -> revisit packaging. A real content dependency appears -> declare that arrow. Standalone installs measurably strand users -> a visible recommended-companion note, never a forced pull.
- Enforced: `.claude-plugin/marketplace.json` (no `dependencies` field on any entry).
