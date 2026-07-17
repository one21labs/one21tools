---
id: 0071
title: "Hooks firing scope: per-project opt-in via the docs/pdca/ marker"
status: accepted
summary: "Resolves ADR 0050's needs-design (issue #212): pdca-workflow's enforcement hooks are per-project opt-in, gated on one adoption marker — the docs/pdca/ dir, scaffolded by /pdca-init and never created by a hook. explicit-model-guard, spawn-log, and adr-lint-post-edit no-op without it; gate-pipe-guard stays as-is (self-scoped by trigger). spawn-log's unconditional mkdir is removed. The parked hooks-only carrier plugin stays parked: self-scoped hooks make the plugin a no-op outside adopting projects, so packaging needs no change. Native enabledPlugins documented as the whole-plugin scoping mechanism."
---

# 0071 — hooks fire per-project, opt-in via docs/pdca/

- Date: 2026-07-17
- Owner: PM
- Panel: advise primitive, 3 fresh advisors with opposing counsel — plugin-adopter (steelman
  per-project; recommended a distinct docs/pdca marker), session-operator (steelman
  session-wide; recommended scoping only spawn-log + documenting enabledPlugins),
  lean-process-engineer (neutral; recommended scoping both behavioral hooks on one marker).
  Split panel — a genuine dialectic, no unanimity-mis-scope signal.
- Context: ADR 0050 settled the hooks as dev tooling for PDCA-adopting repos and left WHERE they
  fire needs-design (issue #212, deferred in PRs #208/#210). As shipped, explicit-model-guard
  denied unmodeled Agent/Task calls in EVERY project the plugin reached, and spawn-log mkdir'd
  docs/pdca/ + wrote a log into any project where a panel primitive (or the builtin `verify`
  skill, an accepted name collision) fired.

## Decision
1. **Per-project opt-in, one adoption marker: `docs/pdca/`.** explicit-model-guard.sh,
   spawn-log.sh, and adr-lint-post-edit.sh exit 0 unless `$CLAUDE_PROJECT_DIR/docs/pdca` exists.
   gate-pipe-guard.sh is unchanged — it only matches invocations of the plugin's own gate
   (adr-lint.mjs), which a non-adopting project never runs.
2. **A hook never creates the marker.** spawn-log's `mkdir -p` is removed; it logs only where
   docs/pdca/ already exists. A hook that mkdir'd its own opt-in marker would opt every project
   in on the first builtin-`verify` invocation — the exact write-pollution ADR 0050 rules out.
3. **`/pdca-init` scaffolds the marker** (docs/pdca/ + committed empty session-log.txt), making
   adoption one explicit step; its SKILL.md states no-marker-no-hooks.
4. **The hooks-only carrier plugin stays parked** (ADR 0050's packaging revisit, discharged):
   self-scoped hooks make pdca-workflow a no-op outside adopting projects, so there is nothing a
   separate carrier would fix.
5. **Native per-project `enabledPlugins` documented** (plugin README) as the mechanism for
   scoping the whole plugin, skills included — orthogonal to hook self-scoping.

## Justification
The marker choice is the contested core. `docs/decisions/` (the shipped adr-lint-post-edit
pattern, lean's one-marker preference) is a generic ADR convention: a stranger's repo with plain
ADRs would silently opt into agent-call denial and house-rule lint blocks — the adopter's
false-positive class, and precisely the "guards they did not ask for" ADR 0050 forbids.
`docs/pdca/` is plugin-owned state (the spawn-log home), unambiguous, already tracked in this
repo, and costs one pdca-init scaffold line. One marker uniformly applied answers lean's
drift concern (adr-lint-post-edit's remaining docs/decisions check is input-existence, not a
second adoption signal). The operator's silent-no-op worry is bounded: where the practice was
never adopted, no guard was ever promised — and the guard's absence is diagnosable from one
documented rule. Ships with updated decision-logic tests only (36 sh + 12 mjs cases green); no
fresh verifier/red-team pass — reversible tooling under owner PR review, and stacking
adversaries on a tested three-line-per-hook change is ceremony (ADR 0062's escalation is for
high-stakes/irreversible).

## Assumptions
- [checkable] the three gated hooks no-op without the marker and behave unchanged with it —
  owner: gates; result: verified (test-spawn-log.sh case 11, test-adr-lint-post-edit.sh fixture
  D, explicit-model-guard.test.mjs no-marker case; all suites green 2026-07-17).
- [checkable] this repo keeps qualifying: docs/pdca/session-log.txt is git-tracked — verified
  (`git ls-files docs/pdca/`).
- [unverifiable] WEAKEST: no existing adopter relies on the old session-wide firing or on
  spawn-log auto-creating docs/pdca/ (adopter population beyond this repo unknown). REOPEN-IF a
  real adopter reports a guard went silent after upgrade — the fix is their one-line
  `mkdir docs/pdca` + commit, and pdca-init already scaffolds it for new adopters.

## Rejected alternatives
- **docs/decisions/ as the marker** (lean) — generic-convention false positive; see above.
- **Scope only spawn-log, keep the deny-guards session-wide** (operator) — leaves
  explicit-model-guard imposing tier discipline on repos that never opted in, contradicting ADR
  0050's settled judgment; "read-only" does not make a deny unobtrusive.
- **enabledPlugins alone, no code change** — detection-shaped: correctness rides on every
  operator hand-scoping every install forever, and freezes the 1-of-4 self-scoping
  inconsistency.
- **Unpark the hooks-only carrier** — unanimous reject; mechanism-first (ADR 0050), and item 4
  above removes its rationale.

## Revisit triggers
- A real adopter reports expecting the hooks without running /pdca-init -> reconsider a visible
  adoption prompt (never auto-opt-in).
- A second marker or per-hook opt-in demand appears -> revisit granularity before adding flags.
- The plugin gains a hook that must fire pre-adoption (e.g. an install-health check) -> that
  hook documents its own exemption here first.
