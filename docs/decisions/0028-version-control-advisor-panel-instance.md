---
id: 0028
title: "one21tools version-controls its own advisor panel (revises 0004's per-call scope)"
status: accepted
tier: lite
summary: "This framework repo adopts a tracked, tested, maintained advisor panel in .claude/agents/ (4 tuned lenses: lean-process-engineer, plugin-adopter, process-economist, session-operator) + 0004's gitignore negation. Dogfooding, NOT a canonical panel for consumers. Tested via char-budget gate extension + a name-matches-filename adr-lint check; maintained via docs/decisions/panel.md roster. Revises 0004's framework-repo per-call clause; enabled by 0016's cost collapse."
---

# 0028 — version-control this repo's advisor panel

- Decision: version-control this repo's own 4-advisor panel (`.claude/agents/`) + keep the
  `.gitignore` negation — one21tools' own tuned lenses, not a canonical panel for consumers
  (they generate their own via `/pdca-init`). Tested by extending `oversizeAgents()` to scan
  `.claude/agents/` and a name-matches-filename adr-lint check over both agent homes.
  Maintained via a `docs/decisions/panel.md` roster; prune-if-unused stays a revisit trigger,
  not machinery.
- Why: 0016 made `/advise` cheap and model-invocable; re-improvising the same ~4 lenses each
  call is derivation muda a tracked panel removes. Deterministic gates only — a behavioral smoke
  test spawning agents is flaky recurring cost the dogfood already pays free.
- Rejected: a behavioral smoke test (non-deterministic); a `Panel:`-line gate (free-text tokens
  false-fire); badging this "the standard panel" for consumers (misleads); prune-telemetry now
  (none exists).
- Reopen-if: the next 4 contestable ADRs name zero standing advisors on their `Panel:` line ->
  tracked-and-ignored, revert or add a forcing function.
- Enforced: `oversizeAgents(".claude/agents")` in char-budget.mjs + the name-matches-filename
  check in adr-lint.mjs; roster at `docs/decisions/panel.md`.
