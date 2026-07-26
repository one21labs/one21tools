---
id: 0005
title: "Wire Claude Code built-in skills into the plugin's execution seams"
status: accepted
tier: lite
summary: "Always-applicable built-ins are named as defaults at their seams (/simplify at the muda-apply step, matching /code-review at the gate); run-coupled built-ins (/verify, /run, /run-skill-generator) stay scoped examples beside the existing 'runnable surface' conditional, never unconditional defaults — preserving ADR 0002's portability."
---

# 0005 — wire built-in skills into the execution seams

- Decision: always-applicable, app-agnostic built-ins are named as the default at one home,
  matching `/code-review`: `/simplify` at `retrospect/SKILL.md` step 6. Run-coupled built-ins
  (`/verify`, `/run`, `/run-skill-generator`) stay scoped examples beside the existing
  "runnable surface" conditional at `verifier.md:26`, never unconditional defaults.
- Why: `/code-review`'s precedent shows naming an always-applicable built-in is right;
  promoting app-coupled ones to defaults would re-introduce the stack coupling ADR 0002 removed.
- Rejected: hard-wire all five as defaults (reintroduces 0002's coupling) — do nothing (leaves the
  `/code-review` inconsistency) — duplicate pointers into claude-md-template.md.
- Reopen-if: a named built-in is renamed/removed — a consumer finds the seam too implicit to
  discover the built-ins.
- Enforced: `pdca-workflow/skills/retrospect/SKILL.md` (step 6),
  `pdca-workflow/agents/verifier.md` (:18, :26).
