---
id: 0082
title: "MSH-baby ships as a pdca-workflow plugin command (first commands/ surface)"
status: accepted
tier: lite
summary: "/pdca-workflow:MSH-baby ('Make Shit Happen') — ship ONE highest-value work item end to end, autonomously, per invocation — lives at pdca-workflow/commands/MSH-baby.md so every installer gets it. Command, not skill: it must never be model-invoked (the inverse of ADR 0016's primitives), and a command adds no always-loaded description. Namespaced invocation accepted by the owner (plugin commands cannot be bare-named). Body stays thin — it defers to the consumer repo's CLAUDE.md rather than restating process rules."
---

# 0082 — MSH-baby plugin command

- Decision: `pdca-workflow/commands/MSH-baby.md`, user-typed only: take the arguments as the
  target or survey the repo's open work, ship exactly one item under the consumer repo's
  standing rules, close with the shipped/value/owner-action summary; name the runner-up,
  don't start it.
- Why: owner-requested for all installers. ADR 0016 rejected commands for the panel primitives
  BECAUSE they must be model-invocable; this surface is the inverse (human-only trigger for
  autonomous spend), so the same reasoning lands on a command.
- Verified: two headless harness runs (scratch repo, seeded defects) — repo-local and
  namespaced --plugin-dir invocations both executed autonomously, committed, and closed with
  the summary; bare-name plugin invocation confirmed unavailable (docs + test).
