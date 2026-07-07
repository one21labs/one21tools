---
id: 0016
title: "Extract advise/verify/red-team as standalone, model-invocable panel primitives"
status: accepted
summary: "The /decide panel's three mechanisms ship as standalone pdca-workflow skills — advise (fresh unprimed advisors), verify (independent gate), red-team (adversary) — invocable situationally by the main agent or the user WITHOUT the full ceremony (no disable-model-invocation). /decide keeps its explicit-invoke restriction and becomes the composition + the ADR record; spawn/shape mechanics move to their one home in each primitive. Trade accepted: three always-loaded descriptions buy right-sized verification; REOPEN-IF a primitive auto-fires wastefully."
---

# 0016 — standalone panel primitives (advise / verify / red-team)

- Date: 2026-07-07
- Owner: PM
- Panel: owner-direct in a cross-repo review session — the owner asked for right-sized, situational panel pieces with the invoke-only restriction lifted; gates (validate.py over the skills, adr-lint) ran as Check.
- Context: the panel's mechanisms existed ONLY inside `/decide` (skills/decide/SKILL.md), which is explicit-invoke and spends 10+ agents + writes ADRs. A judgment call too small for the ceremony — "check this claim independently", "argue this two-sided call" — had no supported path; the main agent could not reach the machinery at all (`disable-model-invocation`). All-or-nothing verification is unused verification.

## Decision
1. **Three new skills in pdca-workflow/skills/**: `advise` (frame -> pick panel from `.claude/agents/` -> spawn fresh/parallel/unprimed -> terse effort x risk x value + tagged assumption; caller decides), `verify` (state claim set -> fresh `verifier` agent -> PASS/BLOCK; verified findings stand), `red-team` (hand candidate + artifacts -> fresh `red-team` agent -> every break answered or folded). Each wraps the existing agent — no new agents, no new roles.
2. **Model-invocable** — none carries `disable-model-invocation`. Each spawns 1-3 agents (bounded, unlike the full panel); descriptions state tight "Use when" triggers so they fire on genuine need. The main agent and the user choose the piece the situation needs.
3. **/decide becomes the composition.** It keeps: explicit-invoke, Inherit/Frame/Decide/Record, the roles table, BLOCK semantics. Its steps now invoke the primitives; spawn/shape mechanics moved to their ONE home in each primitive (the advisor-shape rule, the handoff-overwrite rule) — decide references, never restates. Net body shrink.
4. **Escalation edge stays sharp:** a call that must be recorded (roadmap/product/policy) escalates to `/decide` — the `advise` skill says so; deciding without a record is drift.

## Justification
Right-sizing: most verification-worthy moments are smaller than a roadmap call; a primitive at 1-3 agents makes the Check step cheap enough to actually run. One-home: the spawn/selection rules sat inside a near-cap decide body; each now lives once, in its primitive, and decide references it. Cost is bounded and known: the three descriptions are always-loaded context; the panel machinery itself still loads on demand.

## Assumptions
- [verified] the three descriptions cost 777 chars of always-loaded context combined (289 + 235 + 253; each under the description cap) — the flexibility buys more than three sentences cost.
- [checkable] decide's body shrank below its pre-extraction size while keeping every hard rule reachable (each moved rule cited at its new home) — owner: gates (validate.py body cap) + verifier diff; result: green.
- [checkable] all four skills pass validate.py (trigger-start descriptions, caps) — owner: gates; result: green.
- [unverifiable] model-invocation fires helpfully, not wastefully — REOPEN-IF: a primitive auto-fires on unrelated turns or burns agents unasked; then re-add `disable-model-invocation` to the offender (one line), keeping the others open.

## Rejected alternatives
- Keep everything inside /decide — the status quo; makes the Check step all-or-nothing, so small calls skip verification entirely.
- Commands instead of skills — a command cannot be model-invoked; the point is the MAIN AGENT reaching the machinery mid-task, not only the user.
- Extract `pm`/decision-making as a primitive too — deciding without recording invites unrecorded decisions; the decider stays fused to the ADR ceremony.
- Keep `disable-model-invocation` on the primitives — preserves the failure the owner named: the agent that sees the need cannot act on it.

## Revisit triggers
- A primitive auto-fires wastefully (see REOPEN-IF) -> restore its invoke-only flag.
- The primitives' descriptions grow or multiply -> re-audit always-loaded cost vs use.
- Claude Code ships per-skill invocation budgets/telemetry -> replace the judgment call with measured fire-rates.
