---
id: 0065
title: "Pre-run signal discipline: saturation/floor pre-screen + design-for-signal rules"
status: accepted
summary: "Adopt the saturation/floor pre-screen as a standard pre-run rule (#178) and fold the owner design directives (variance-as-metric, powered designs) plus ADR 0062's gate-or-optimization field into pre-registration.md as a Design-for-signal section. Doc rule + /bench guardrail rung now; a standing lib gate only if the doc rung fails. Closes #178 and #184."
---

# 0065 — pre-run signal discipline

- Date: 2026-07-15
- Owner: PM
- Panel: none — routine, reversible doc/checklist change; recorded directly per ADR 0062's
  two-stage routing. The two design directives are owner directives (#184, 2026-07-13) —
  DECIDED inputs recorded, not re-litigated.
- Context: #172-I1 shipped a ceilinged eval — the bare arm recalled 0.83–1.0 because the
  substrates restated the violated rules; verdict INCONCLUSIVE, the grid's spend carried no
  signal (`benchmarks/2026-07-12-pdca-retrospect-recall/README.md`). The mirror failure
  floored three benchmarks (ADR 0025). The countermeasure existed as prose in #41's
  pre-registration comment but was never promoted to a standing home, and #172-I1's pre-reg
  did not inherit it. Separately, #184's residue holds two owner design directives with no
  standing home, and ADR 0062 d2 mandates a "gate or optimization?" pre-reg field not yet
  landed.

## Decision
1. **Saturation/floor pre-screen is a standard pre-run rule.** A cheap control-arm screen,
   recorded in the dated dir before any grid spends, drops or hardens evals sitting outside
   their discriminating band. Mechanics + threshold shape live at their home,
   `skills/building-skills/references/pre-registration.md`; operational rung: a /bench
   Guardrails bullet (`skill-bench/skills/bench/SKILL.md`). The rule text carries the ADR 0024
   guardrail verbatim: restore discriminating power, never difficulty-tune toward a verdict.
2. **Design-for-signal section in pre-registration.md**, three rules: the mandatory "gate or
   optimization?" field (implements ADR 0062 d2); variance as a primary metric (pre-register
   per-arm consistency alongside mean deltas); powered designs (size reps/scenarios from
   measured variance components, state the minimum detectable effect).
3. **Mechanization is deferred to the first consumer.** #177 already pre-registers an
   in-harness mechanized pre-screen (~0.75 threshold guidance); a standing `lib` hard-gate
   ships only through this ADR's revisit trigger, not now.

Falsifiable criterion: the next two paid grids' pre-registrations each record a pre-screen
result before spend and state variance metric + MDE. REOPEN-IF a grid again reaches verdict on
an eval discovered ceilinged/floored only after spend — that falsifies "doc rule + checklist
rung suffices" and promotes the pre-screen to a mechanized lib gate.

## Justification
Cost ~0 (doc + one checklist bullet) against a twice-observed class that wasted a full grid's
spend. The pre-screen is 1 rep x control only — it reorders spend like cost-pilot-first, adds
none. The directives and the 0062 field are already-decided inputs needing only a standing
home; folding them into the same pre-run doc keeps one home for pre-registration content
rules.

## Assumptions
- [verified] the incident base: #172-I1's ceiling and diagnosis are recorded in
  `benchmarks/2026-07-12-pdca-retrospect-recall/README.md` (Results/diagnosis); the #41
  pre-registration comment holds the unpromoted prose precedent.
- [checkable] a standing-doc rule + /bench guardrail is inherited by the next pre-reg, unlike
  the issue-comment precedent. TEST: #177's pre-registration shows a recorded pre-screen
  before its grid. — owner: #177. result: pending.
- [unverifiable] a 1-rep control screen detects saturation reliably enough (rep variance can
  slip a ceilinged eval past one rep). Accepted: the screen is a cheap filter, not proof;
  grids keep the per-expectation ceiling diagnostic post-hoc. REOPEN bounded by the criterion
  above.

## Rejected alternatives
- **Decline (option c)** — the class is twice-observed and burned real spend; accepting it
  contradicts ADR 0024's cost discipline.
- **Standing benchmarks/lib hard-gate now (option b's mechanized half)** — no generic scoring
  interface exists across harnesses (each experiment's metric differs); a gate without a
  consumer is gold-plate. #177 mechanizes in-harness where the first consumer lives; the
  revisit trigger promotes it if the doc rung fails.
- **Home the rule in the bench SKILL.md only** — pre-registration.md is the method home the
  bench skill explicitly references instead of restating; non-bench experiments pre-register
  too.

## Revisit triggers
- The falsifiable criterion fires (post-spend ceiling/floor discovery) -> mechanize as a lib
  gate with its own decision-logic test (Never rule).
- #177's pre-screen drops or hardens most of its substrates -> the ~0.75 ceiling-threshold
  guidance is miscalibrated; revisit the guidance, not the rule.
