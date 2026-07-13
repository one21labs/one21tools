---
id: 0055
title: "skill-bench plugin: extract the measurement harness, add a cross-family judge and a rented execution substrate"
status: proposed
summary: "Extract the hermetic skill-measurement harness into a standalone `skill-bench` marketplace plugin per #170, and fold in two capabilities the #172 evidence justifies: (1) a CROSS-FAMILY judge (default grok-4.5) as a first-class grader, after a 72-cell prototype showed the same-family opus judge inflated absolute rates ~20pp and widened the panel's measured edge from +0.010 to +0.125 (magnitude, not sign); (2) a rented execution SUBSTRATE (promptfoo/Inspect AI) under the bespoke causal+pre-registration layer no vendor sells. DRAFT for /decide — not yet accepted."
---

# 0055 — skill-bench plugin: extraction + cross-family judge + rented substrate

- Date: 2026-07-13
- Owner: PM (DRAFT — needs the /decide panel: plugin-adopter, process-economist, session-operator, red-team)
- Context: #170 planned extracting the repo's unique asset — the only public hermetic skill-measurement pipeline — but predated two findings. (a) The #172 "Claude grades Claude" caveat is now quantified: a cross-family re-grade of I2's 72 blinded cells with grok-4.5 (normalization held fixed; same rubric; grade+prosecute) found the same-family opus judge ~20pp more lenient (met-rate 0.747 vs 0.552; 57/58 disagreements one-directional; kappa 0.575), and the verdict JUDGE-DEPENDENT: C-B widened +0.010 (opus) -> +0.125 (grok), and an exp-2 ceiling that hid a panel edge under opus broke under grok (C 0.83 vs B 0.54). (b) A framework survey found no commercial eval tool (promptfoo, Inspect AI, Braintrust, LangSmith, OpenAI/Anthropic) offers arm isolation, prosecutor grading, or pre-registration — yet all offer tracing, dataset versioning, and CI gating the stdlib harness lacks.

## Decision (proposed)

1. **Extract per #170's milestones (M1-M6 unchanged): a `skill-bench` plugin** housing `benchmarks/lib/*` + tests, the trigger runner (`run_eval.py`/`eval_verdict.py`), the method references (one home; `building-skills` then references, SSoT), and one canonical grading-workflow template. `validate.py` and the dated `benchmarks/<date>-*/` records stay put (authoring tool / append-only evidence).

2. **Add a cross-family judge as a first-class, DEFAULT-ON grader.** The grading template takes `--judge` (default `grok-4.5` via headless `-p --json-schema`, tools denied; `claude`/opus for same-family A/B). The prototype proves the judge changes the verdict, and Anthropic's own eval guidance recommends a different-family grader. On divergence, surface it (that IS the finding) via a standard `judge-divergence` diagnostic (concordance + kappa), don't average.

3. **Adopt a rented execution substrate under the bespoke layer, not instead of it.** Wrap `promptfoo` (npx, cheap CI gating) as the default runner behind the `hermetic_driver` interface; keep an `inspect-ai` option and a `claude -p`/`grok -p` fallback. The causal layer (arms, blind.py, cost_gate, verdict.py, prosecutor, pre-registration) stays on top — the differentiator.

4. **UX: explicit-invoke commands with an up-front cost gate and a two-judge default.**
   - `/bench-skill <dir> [--judge grok|claude|both] [--substrate promptfoo|inspect|native]` — paired hermetic value benchmark; prints a cost estimate and asks for confirmation BEFORE any paid run (spend guard, #170 hard-problem 1).
   - `/trigger-test <dir>` — description ablation (TP/FP).
   - `/bench-verdict <results> [--judge ...]` — re-run verdict math (incl. cross-family re-grade) on existing results with NO new generation spend — the exact prototype flow, generalized.

## Justification
The extraction was already planned (#170); this ADR adds the two capabilities the new evidence demands. Cross-family judging is default-on because same-family judging is now a MEASURED confound — its value is bias-reduction, NOT cost (grok and Claude are both marginally free here; runs are priced notionally at published rates by deterministic `costing.py`). Renting the substrate keeps the parts no vendor sells while dropping hand-rolled matrix plumbing; wrapping (not replacing) keeps M1's move behavior-neutral.

## Assumptions
- **[checkable] WEAKEST: the grok CLI is a viable programmatic judge.** Verified 2026-07-13 by the 72-cell prototype (0 errors, schema-constrained structured output, grade+prosecute). CAVEAT: normalization was held on Claude (a residual same-family surface) — a fuller version cross-families the normalizer too. TEST before shipping the judge default: re-run one dated benchmark's grading through the grok judge and confirm the divergence diagnostic reproduces.
- **[checkable] the installed grok build exposes `--json-schema`, `--prompt-file`, `--agents`, and a `structuredOutput` JSON envelope** even though the public docs (docs.x.ai) do not — verified empirically from `grok --help` and live calls; the binary leads the docs. Pin the build; re-verify on grok update.
- [checkable] no commercial eval tool offers arm isolation / prosecutor / pre-registration — verified by the 2026-07-13 framework survey (Braintrust/LangSmith/OpenAI/Anthropic report aggregate pass rates only; none does CIs).
- [unverifiable] a rented substrate reduces net maintenance vs the stdlib harness. REOPEN-IF the promptfoo adapter costs more to maintain than the runner it replaces.

## Consequences / sequencing
- Interacts with #150 / ADR 0050 (per-plugin source split) — resolve the dependency shape at M0 (does skill-bench declare pdca-workflow? likely no).
- Reframes #179: the I2 null is judge-dependent and leans KEEP under grok — the routing /decide must weigh the cross-family result, not just the opus grid.
- New follow-up issues: (i) cross-family judge integration + divergence diagnostic; (ii) promptfoo/inspect substrate adapter behind hermetic_driver; (iii) re-grade the frozen dated benchmarks through the grok judge to test whether other verdicts are judge-dependent.
