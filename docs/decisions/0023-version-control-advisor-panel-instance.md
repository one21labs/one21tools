---
id: 0023
title: "one21tools version-controls its own advisor panel (revises 0004's per-call scope)"
status: accepted
summary: "This framework repo adopts a tracked, tested, maintained advisor panel in .claude/agents/ (4 tuned lenses: lean-process-engineer, plugin-adopter, process-economist, session-operator) + 0004's gitignore negation. Dogfooding, NOT a canonical panel for consumers (they generate their own). Tested = extend the char-budget gate to .claude/agents/ + a static name-matches-filename adr-lint check. Maintained = a docs/decisions/panel.md roster; prune-if-unused stays a revisit trigger. Revises 0004's framework-repo per-call clause (its consumer guidance stands); enabled by 0016's cost collapse (advise now cheap, model-invocable)."
---

# 0023 — version-control this repo's advisor panel

- Date: 2026-07-08
- Owner: PM
- Panel: the 4 candidate advisors, unprimed, on their own adoption (dogfood + smoke test) — lean-process-engineer (muda), process-economist (cost), session-operator (realism), plugin-adopter (consumer). verifier + red-team gate next.
- Context: `.claude/agents/*.md` (4 tuned advisors) sit untracked despite 0004's `!.claude/agents/` negation (`.gitignore:14`); the `advise` skill sources its panel there (`advise/SKILL.md:16`) but falls back to generic opposing counsel when absent. 0004 scoped this framework repo per-call/no-standing-roster — before 0016 made `/advise` a cheap, model-invocable primitive. Open: adopt a standing panel, kept non-muda (0013-0022 Panel: lines named zero standing advisors — text alone was bypassed)?

## Decision
1. **Version-control this repo's OWN 4-advisor panel** in `.claude/agents/` + keep the negation. These are one21tools' tuned lenses (framework-author concerns), NOT a canonical panel for consumers — the shipped scaffold stays at pdca-init's `advisor-template` home; consumers generate their own (panel-generation warns a borrowed panel gives confident-but-irrelevant advice). Membership: the 4 stay — non-overlapping lenses matching this repo's recurring axes (cost/muda/adoption/realism, per 0002-0006 Panel: recurrence).
2. **Tested (deterministic only):** (a) extend `oversizeAgents()` to also scan `.claude/agents/` (reuses the injectable-`dir` predicate, `char-budget.mjs:73`; + fixture test); (b) a static `name:`-matches-filename check in adr-lint's agent pass over BOTH agent homes (the plugin meta-roles `pdca-workflow/agents/` and this panel `.claude/agents/`; mirrors the id-matches-filename ADR guard), so a renamed/malformed agent fails the gate. Whether the panel is actually CONSULTED is not CI-observable — that lives in the `[unverifiable]` revisit trigger, not a gate; parsing free-text `Panel:` lines is rejected (below). No behavioral smoke test, no full frontmatter validator.
3. **Maintained:** add `docs/decisions/panel.md` — the roster + one line per lens on why this repo needs it + PM ownership (panel-generation's own method). Git history is the SSoT for changes; no changelog. Prune-if-unused is a REVISIT TRIGGER, not machinery (no per-skill telemetry exists — 0016:39 defers it).
4. **Record:** this ADR; 0004's framework-repo per-call clause is rationalized in place to cite 0023; 0004's consumer guidance is untouched.

## Justification
0016 collapsed the invocation cost 0004 couldn't weigh — per-call was right when the panel loaded only via the 10+-agent `/decide`; a cheap model-invocable `/advise` flips the use/cost ratio — and re-improvising the same ~4 lenses each call is re-derivation muda a tracked panel removes. Deterministic gates only: the repo's rule is "the deterministic parts are real scripts", so a CI smoke test that spawns agents is flaky + a recurring cost the dogfood pays free. Whether the panel gets consulted isn't CI-observable, so that risk (0013-0022 bypassed it) lives in the weakest `[unverifiable]` trigger, not a fragile `Panel:`-line regex.

## Assumptions
- [checkable] `oversizeAgents(".claude/agents")` + the name-matches-filename agent check land with passing tests and adr-lint stays green on the corpus — owner: gates (`node --test`, adr-lint); result: pending.
- [checkable] the 4 panel files are tracked (`git ls-files .claude/agents`) and each is under AGENT_CHAR_BUDGET (3000; all ~1.7k now) — owner: gates; result: pending.
- [checkable-doc] `.claude/agents/` is Claude Code's project-agent discovery dir (so the negation keeps discovery and a consumer copying these gets author-lenses) — the "own panel, not shipped standard" reframe holds — PM verified vs `advise/SKILL.md:16` + panel-generation.
- [unverifiable] WEAKEST: a tracked panel actually gets consulted, not bypassed like 0013-0022 — REOPEN-IF the next 4 recorded ADRs with a contestable call name zero standing advisors on their `Panel:` line; then adoption is tracked-and-ignored — revert to per-call or add a stronger forcing function.

## Rejected alternatives
- Behavioral smoke test (spawn each, assert output shape) — non-deterministic in CI, recurring spend; the dogfood exercises them free.
- A `Panel:`-line gate (hard or soft) — free-text lines carry kebab tokens (`owner-direct`, `cross-repo`) that false-fire; consultation is the `[unverifiable]` trigger's job, not a regex.
- Badge it "THE standard panel" for consumers — a borrowed panel misleads; these are author-lenses. Consumers generate their own via `/pdca-init`.
- Build prune-if-unused telemetry now — no invocation telemetry exists (0016:39); speculative machinery.

## Revisit triggers
- The next 4 contestable ADRs name zero standing advisors -> tracked-and-ignored; revert or add a forcing function.
- Claude Code ships per-skill invocation telemetry -> replace the judgment prune-guard with measured fire-rates (per 0016).
- The advisor shape-contract (duplicated across the 4 files + `advise/SKILL.md:22`) diverges -> add a guard then, not now.
