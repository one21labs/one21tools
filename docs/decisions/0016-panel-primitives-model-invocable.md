---
id: 0016
title: "Standalone, model-invocable panel primitives: advise/verify/red-team; retrospect joins the set (trigger-bound)"
status: accepted
tier: lite
summary: "The /decide panel's three mechanisms ship as standalone pdca-workflow skills — advise (fresh unprimed advisors), verify (independent gate), red-team (adversary) — invocable situationally without the full ceremony (no disable-model-invocation). Retrospect joins the set, trigger-bound to ADR 0081. /decide becomes the composition + the ADR record. REOPEN-IF a primitive auto-fires wastefully."
---

# 0016 — standalone panel primitives (advise / verify / red-team)

- Date: 2026-07-07
- Decision: three new pdca-workflow skills — `advise` (fresh/parallel/unprimed advisors), `verify` (fresh `verifier` agent, PASS/BLOCK), `red-team` (adversary, every break answered or folded) — each wraps an existing agent, none carries `disable-model-invocation`, so the main agent and user reach right-sized verification without the full `/decide` ceremony. `/decide` becomes the composition, invoking the primitives rather than restating their mechanics. Amended 2026-07-20 (#260): `retrospect` joins the set, TRIGGER-BOUND to ADR 0081 — the invoke-only flag forced every autonomous closeout down the raw-agent path, reading compliance as zero structurally, not behaviorally.
- Why: most verification-worthy moments are smaller than a roadmap call; a 1-3 agent primitive makes Check cheap enough to run. Spawn/selection rules moved into each primitive (one-home).
- Rejected: keep everything inside /decide — all-or-nothing Check. Commands instead of skills — can't be model-invoked. Keep `disable-model-invocation` — preserves the exact failure being fixed.
- Reopen-if: a primitive auto-fires wastefully -> restore its invoke-only flag, keeping the others open.
- Enforced: `pdca-workflow/skills/advise/SKILL.md`, `pdca-workflow/skills/verify/SKILL.md`, `pdca-workflow/skills/red-team/SKILL.md` (no `disable-model-invocation`).
