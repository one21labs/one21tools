---
id: 0016
title: "Standalone, model-invocable panel primitives: advise/verify/red-team; retrospect joins the set (trigger-bound)"
status: accepted
tier: lite
summary: "The /decide panel's three mechanisms ship as standalone, model-invocable pdca-workflow skills — advise, verify, red-team — usable without the full ceremony. Retrospect joins trigger-bound to ADR 0081; bench joins once its paid paths are spend-guarded. /decide becomes the composition + the ADR record."
---

# 0016 — standalone panel primitives (advise / verify / red-team)

- Decision: three new pdca-workflow skills — `advise`, `verify`, `red-team` — each wraps an existing agent and none carries `disable-model-invocation`, so the main agent and user reach right-sized verification without the full `/decide` ceremony. `/decide` becomes the composition, invoking the primitives rather than restating their mechanics. Amended 2026-07-20 (#260): `retrospect` joins, TRIGGER-BOUND to ADR 0081 — the invoke-only flag pushed every autonomous closeout down the raw-agent path, reading compliance as zero structurally, not behaviorally. Amended 2026-07-26 (owner): `bench` joins, conditional on every paid path carrying a refusal the model cannot skip by accident.
- Why: most verification-worthy moments are smaller than a roadmap call, and a 1-3 agent primitive makes Check cheap enough to actually run. Spawn rules live in each primitive (one-home).
- Rejected: keep everything inside /decide — all-or-nothing Check. Commands instead of skills — can't be model-invoked. Keep the flag — preserves the exact failure being fixed.
- Reopen-if: a primitive auto-fires wastefully -> restore its invoke-only flag, keeping the others open.
- Enforced: `pdca-workflow/skills/advise/SKILL.md`, `pdca-workflow/skills/verify/SKILL.md`, `pdca-workflow/skills/red-team/SKILL.md`, `pdca-workflow/skills/retrospect/SKILL.md`, `skill-bench/skills/bench/SKILL.md`, `pdca-workflow/skills/decide/SKILL.md` (none carries `disable-model-invocation`).
