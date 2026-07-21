---
id: 0082
title: "MSH-baby ships as a pdca-workflow plugin command (first commands/ surface)"
status: accepted
summary: "/pdca-workflow:MSH-baby ('Make Shit Happen') — ship ONE highest-value work item end to end, autonomously, per invocation — lives at pdca-workflow/commands/MSH-baby.md so every installer gets it. Command, not skill: it must never be model-invoked (the inverse of ADR 0016's primitives), and a command adds no always-loaded description. Namespaced invocation accepted by the owner (plugin commands cannot be bare-named). Body stays thin — it defers to the consumer repo's CLAUDE.md rather than restating process rules."
---

# 0082 — MSH-baby plugin command

- Date: 2026-07-21
- Owner: PM (owner-directed; the want is quoted: a typed command that "just executes" one item, "available to anyone who installs pdca-workflow")
- Panel: none (routine, owner-settled scope; recorded directly)
- Context: the owner wants a one-keystroke autonomous mode. Bare `/MSH-baby` is impossible for a plugin-shipped command — plugin commands are always namespaced (official plugin docs; reproduced: bare invocation returns Unknown command) — and the owner accepted the namespaced form over a repo-local alias.

## Decision
`pdca-workflow/commands/MSH-baby.md`, user-typed only: take the arguments as the target or survey the repo's open work, ship exactly one item under the consumer repo's standing rules, close with the shipped/value/owner-action summary; name the runner-up, don't start it.

## Justification
ADR 0016 rejected commands for the panel primitives BECAUSE they must be model-invocable; this surface is the inverse (human-only trigger for autonomous spend), so the same reasoning lands on a command. Thin body: process rules live in the consumer repo's CLAUDE.md (one home) — a command restating them would drift. No enforcing gate is added: a prompt file has no decision logic to test (the "Never" rule covers process-gating scripts), and an existence-check would be a vacuous gate (ADR 0069) — hence full tier, not lite.

## Assumptions
- [checkable] the plugin-shipped command resolves and executes end to end — owner: headless harness (scratch repo, seeded defects, `--plugin-dir`); result: verified — namespaced run fixed all defects, committed, closed with the summary; repo-local content run identical; bare-name run Unknown-command.
- [unverifiable] the one-item scope and no-permission-asking discipline hold in real consumer sessions (the harness target was a toy) — REOPEN-IF a run starts a second item, wanders past its target, or stops to ask on reversible steps; then tighten the body's scope clause.

## Rejected alternatives
- Skill (skills/msh-baby/SKILL.md) — burns an always-loaded description in every consumer session for a surface that must never model-fire; forces a lowercase name.
- Repo-local `.claude/commands/` only — not delivered to installers; the owner's later directive supersedes it.
- Plugin command + repo-local bare-name alias — offered; owner chose namespaced-only (no duplicate to drift).

## Revisit triggers
- Claude Code ships bare-name or aliasable plugin commands → revisit the original bare `/MSH-baby` want.
- A run violates one-item scope or omits the closing summary → tighten the body; consider trigger-testing the wording (ADR 0033 machinery).
