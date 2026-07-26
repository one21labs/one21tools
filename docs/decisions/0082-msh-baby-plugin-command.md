---
id: 0082
title: "MSH ships as a pdca-workflow plugin command (first commands/ surface)"
status: accepted
summary: "/pdca-workflow:MSH ('Make Shit Happen') — ship ONE highest-value cohesive work package end to end, autonomously, per invocation; extra issues batch only by owner declaration or necessity coupling, each declared in the PR body. Lives at pdca-workflow/commands/MSH.md. Command, not skill: must never be model-invoked, adds no always-loaded description. Namespaced (plugin commands cannot be bare-named). Body stays thin, deferring to the consumer repo's CLAUDE.md."
---

# 0082 — MSH plugin command

- Date: 2026-07-21
- Owner: PM (owner-directed: a typed command that "just executes" one item)
- Context: bare `/MSH` is impossible for a plugin-shipped command (plugin commands are always
  namespaced); the owner accepted the namespaced form over a repo-local alias.

## Decision
`pdca-workflow/commands/MSH.md`, user-typed only: take the argument target(s) as the
owner-declared package, or survey the repo's open work; ship exactly ONE cohesive package per
invocation under the consumer repo's standing rules; close with a shipped/value/owner-action
summary; name the runner-up, don't start it. Unit = one cohesive WORK PACKAGE, not one item (owner
amendment, 25-Jul-2026): extra issues batch only by owner DECLARATION in the arguments, or by
NECESSITY coupling with every joiner declared alongside its coupling — a similarity-based cohesion
test was tried and red-teamed to failure. Loosely-related items take ADR 0056's route instead
(successive invocations). The batching wording has ONE home — the command body.

## Justification
ADR 0016 rejected commands for panel primitives BECAUSE they must be model-invocable; this surface
is the inverse (human-only trigger for autonomous spend). Thin body: process rules live in the
consumer repo's CLAUDE.md. No enforcing gate: a prompt file has no decision logic to test.

## Assumptions
- [unverifiable] the one-package scope and no-permission-asking discipline hold in real consumer sessions (the harness target was a toy). REOPEN-IF a run joins an issue whose declared coupling the diff does not substantiate, wanders past its declared package, or stops to ask on reversible steps -> tighten the body's scope clause; the per-joiner declaration is what makes this auditable after the fact.

## Rejected alternatives
- A skill — burns an always-loaded description for a surface that must never model-fire.
- Repo-local `.claude/commands/` only — not delivered to installers.

## Revisit triggers
- Claude Code ships bare-name or aliasable plugin commands -> revisit the bare `/MSH` want.
- A run violates one-package scope, joins an issue without substantiated coupling, or omits the
  closing summary -> tighten the body.
