---
id: 0065
title: "Pre-run signal discipline: saturation/floor pre-screen + design-for-signal rules"
status: accepted
tier: lite
summary: "Adopt the saturation/floor pre-screen as a standard pre-run rule (#178) and fold owner design directives (variance-as-metric, powered designs) plus ADR 0062's gate-or-optimization field into pre-registration.md as a Design-for-signal section. Doc rule + /bench guardrail rung now; a standing lib gate only if the doc rung fails. Closes #178 and #184."
---

# 0065 — pre-run signal discipline

- Decision: (1) the saturation/floor pre-screen — a cheap control-arm screen recorded before any
  grid spends, dropping or hardening evals outside their discriminating band — becomes a
  standard pre-run rule; mechanics live at
  `skills/building-skills/references/pre-registration.md`, operational rung is a `/bench`
  Guardrails bullet — restore discriminating power, never difficulty-tune toward a verdict.
  (2) a Design-for-signal section in pre-registration.md: the mandatory "gate or optimization?"
  field (ADR 0062 d2), variance as a primary metric, powered designs. (3) mechanization deferred
  to the first consumer (#177); a standing lib hard-gate ships only via this ADR's reopen-if.
- Why: cost ~0 against a twice-observed class that wasted a full grid's spend (#172-I1's
  ceilinged eval). The pre-screen is 1 rep x control only — reorders spend, adds none.
- Rejected: declining the countermeasure (contradicts ADR 0024's cost discipline); a standing
  benchmarks/lib hard-gate now (no generic scoring interface across harnesses, gold-plate
  without a consumer); homing the rule in the bench SKILL.md only (non-bench experiments need
  pre-registration.md too).
- Reopen-if: a grid reaches verdict on an eval discovered ceilinged/floored only after spend ->
  mechanize as a lib gate with its own decision-logic test.
- Enforced: pre-registration.md Design-for-signal section; bench SKILL.md Guardrails bullet.
