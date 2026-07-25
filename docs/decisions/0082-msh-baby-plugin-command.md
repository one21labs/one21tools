---
id: 0082
title: "MSH-baby ships as a pdca-workflow plugin command (first commands/ surface)"
status: accepted
summary: "/pdca-workflow:MSH-baby ('Make Shit Happen') — ship ONE highest-value work package end to end, autonomously, per invocation (amended 25-Jul-2026: unit widened from single item to cohesive package; extra issues batch only by owner declaration in the arguments or by red-team-hardened necessity coupling, each declared in the PR body) — lives at pdca-workflow/commands/MSH-baby.md so every installer gets it. Command, not skill: it must never be model-invoked (the inverse of ADR 0016's primitives), and a command adds no always-loaded description. Namespaced invocation accepted by the owner (plugin commands cannot be bare-named). Body stays thin — it defers to the consumer repo's CLAUDE.md rather than restating process rules."
---

# 0082 — MSH-baby plugin command

- Date: 2026-07-21
- Owner: PM (owner-directed; the want is quoted: a typed command that "just executes" one item, "available to anyone who installs pdca-workflow")
- Panel: none (routine, owner-settled scope; recorded directly)
- Context: the owner wants a one-keystroke autonomous mode. Bare `/MSH-baby` is impossible for a plugin-shipped command — plugin commands are always namespaced (official plugin docs; reproduced: bare invocation returns Unknown command) — and the owner accepted the namespaced form over a repo-local alias.

## Decision
`pdca-workflow/commands/MSH-baby.md`, user-typed only: take the argument target(s) as the owner-declared package or survey the repo's open work, ship exactly one cohesive package per invocation under the consumer repo's standing rules, close with the shipped/value/owner-action summary; name the runner-up, don't start it. The operative batching words (necessity coupling, per-joiner declaration) have ONE home: the command body — this record states the decision and defers the wording there (the 0021/0056 pattern), so amending one can never silently strand the other.

## Justification
ADR 0016 rejected commands for the panel primitives BECAUSE they must be model-invocable; this surface is the inverse (human-only trigger for autonomous spend), so the same reasoning lands on a command. Thin body: process rules live in the consumer repo's CLAUDE.md (one home) — a command restating them would drift. No enforcing gate is added: a prompt file has no decision logic to test (the "Never" rule covers process-gating scripts), and an existence-check would be a vacuous gate (ADR 0069) — hence full tier, not lite.

## Assumptions
- [checkable] the plugin-shipped command resolves and executes end to end — owner: headless harness (scratch repo, seeded defects, `--plugin-dir`); result: verified — namespaced run fixed all defects, committed, closed with the summary; repo-local content run identical; bare-name run Unknown-command.
- [unverifiable] the one-package scope and no-permission-asking discipline hold in real consumer sessions (the harness target was a toy) — REOPEN-IF a run joins an issue whose declared coupling the diff does not substantiate, wanders past its declared package, or stops to ask on reversible steps; then tighten the body's scope clause. The per-joiner declaration in the PR body is what makes this tripwire auditable after the fact.

## Rejected alternatives
- Skill (skills/msh-baby/SKILL.md) — burns an always-loaded description in every consumer session for a surface that must never model-fire; forces a lowercase name.
- Repo-local `.claude/commands/` only — not delivered to installers; the owner's later directive supersedes it.
- Plugin command + repo-local bare-name alias — offered; owner chose namespaced-only (no duplicate to drift).

## Amendment (owner, 25-Jul-2026; red-teamed before ship)
Unit widened from one work item to one cohesive work package, on the owner's quoted want:
combine "wherever it makes sense — for efficiency and practicality". The fresh adversary broke
the first draft's similarity-based cohesion tests (review story / revert boundary / surface
overlap): two were satisfiable by construction, and on live pairs the test admitted the wrong
batch while rejecting the intended one. So batching is by DECLARATION or NECESSITY only —
either the owner names several targets in the arguments (ADR 0051's principle: batching is
declared, never inferred), or a joiner is admitted because shipping the lead forces edits to a
file the joiner also needs, or invalidates the joiner's recorded fix. Each joiner is declared
with its coupling in the PR body and closing summary, making the tripwire below fireable.
Loosely-related items take ADR 0056's route instead — successive invocations landing per the
consumer repo's shipping rules (in this repo: the open session PR). Parallel lanes stay scoped
to independence of judgment (advisors/verifiers/red-team) as the consumer repo's rules invoke
them — ADR 0062's panel economics stand; never parallel co-authoring of unrelated items.

## Revisit triggers
- Claude Code ships bare-name or aliasable plugin commands → revisit the original bare `/MSH-baby` want.
- A run violates one-package scope, joins an issue without a substantiated coupling, or omits the closing summary → tighten the body; consider trigger-testing the wording (ADR 0033 machinery).
