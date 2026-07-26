---
id: 0071
title: "Hooks firing scope: per-project opt-in via the docs/pdca/ marker"
status: accepted
summary: "Resolves ADR 0050's needs-design (issue #212): pdca-workflow's enforcement hooks are per-project opt-in, gated on one adoption marker — the docs/pdca/ dir, scaffolded by /pdca-init and never created by a hook. explicit-model-guard, spawn-log, and adr-lint-post-edit no-op without it; spawn-log's unconditional mkdir is removed. The hooks-only carrier plugin stays parked. Native enabledPlugins documented as the whole-plugin scoping mechanism."
---

# 0071 — hooks fire per-project, opt-in via docs/pdca/

- Date: 2026-07-17
- Owner: PM
- Context: ADR 0050 settled the hooks as dev tooling for PDCA-adopting repos but left WHERE they
  fire needs-design (issue #212). As shipped, `explicit-model-guard.sh` denied unmodeled
  Agent/Task calls in EVERY project the plugin reached, and `spawn-log.sh` mkdir'd `docs/pdca/`.

## Decision
1. **Per-project opt-in, one adoption marker: `docs/pdca/`.** `explicit-model-guard.sh`,
   `spawn-log.sh`, and `adr-lint-post-edit.sh` exit 0 unless `$CLAUDE_PROJECT_DIR/docs/pdca`
   exists.
2. **A hook never creates the marker.** `spawn-log.sh`'s `mkdir -p` is removed; it logs only where
   `docs/pdca/` already exists — a hook that mkdir'd its own opt-in marker would opt every project
   in on the first builtin-`verify` invocation.
3. **`/pdca-init` scaffolds the marker** (`docs/pdca/` + a committed empty `session-log.txt`); its
   SKILL.md states no-marker-no-hooks.
4. **The hooks-only carrier plugin stays parked**: self-scoped hooks make pdca-workflow a no-op
   outside adopting projects.
5. **Native per-project `enabledPlugins` documented** (plugin README) for scoping the whole plugin.

## Justification
`docs/pdca/` is plugin-owned state, unambiguous, and costs one pdca-init scaffold line.
`docs/decisions/` (a generic ADR convention) would silently opt a stranger's plain-ADR repo into
agent-call denial and lint blocks — exactly the "guards they did not ask for" ADR 0050 forbids.

## Assumptions
- [unverifiable] WEAKEST: no existing adopter relies on the old session-wide firing or on spawn-log auto-creating `docs/pdca/` (adopter population beyond this repo unknown). REOPEN-IF a real adopter reports a guard went silent after upgrade — the fix is their one-line `mkdir docs/pdca` + commit, and pdca-init already scaffolds it for new adopters.

## Rejected alternatives
- `docs/decisions/` as the marker — generic-convention false positive (see Justification).
- Scope only spawn-log, keep the deny-guards session-wide — leaves explicit-model-guard imposing
  tier discipline on repos that never opted in.
- `enabledPlugins` alone, no code change — correctness rides on every operator hand-scoping forever.

## Revisit triggers
- A real adopter reports expecting the hooks without running /pdca-init -> reconsider a visible
  adoption prompt (never auto-opt-in).
