---
id: 0013
title: "building-skills evals: delegate execution to skill-creator, own the cost verdict"
status: accepted
summary: "Empirical skill evals are HYBRID: execution stays DELEGATED to skill-creator's benchmark harness (paired with/without runs, graded assertions); this repo owns only the thin layer upstream lacks — the evals.json schema gate in validate.py (the REOPEN-IF fired: eval artifacts now exist in-repo) and eval_verdict.py, the cost-per-benefit verdict (Wilson CI + delta per 1k chars of SKILL.md body). No owned PAIRED-BENCHMARK harness (ADR 0033 owns the trigger runner). Keeps: author-separation, fresh independent grader, validate.py authoritative, prose vendored."
---

# 0013 — building-skills evals: delegate execution, own the cost verdict

- Date: 2026-07-04
- Owner: PM
- Panel: original call — opposing counsel (2 sonnet advisors) + neutral harness-design lens, verifier + red-team gate. Verdict-layer amendment — owner-direct in a cross-repo review session (owner stated the requirement); gates (validate.py, unit tests, adr-lint) ran as Check.
- Context: skill-creator's benchmark harness (paired with_skill/without_skill runs, graded assertions, token/time stats) is NOT in this marketplace nor bundled in Claude Code. Char budgets enforce only the COST side of a skill; no mechanism measured whether its content BUYS anything. The owner requires skills be empirically shown to justify their context cost.

## Decision
**Delegate execution; own the schema gate + the verdict. No owned PAIRED-BENCHMARK harness
(ADR 0033 separately vendors and owns the trigger runner) — one concern, one PR.**
1. **Execution stays skill-creator's.** Its benchmark mode already runs the paired baseline with graded assertions and aggregate stats (`aggregate_benchmark` -> `benchmark.json`). Re-building that loop here re-forks an upstream that already superseded itself — gold-plating. The protocol home is `skills/building-skills/references/empirical-evals.md` (install pointer, authoring disciplines, run recipe, verdict).
2. **Schema gate (the fired REOPEN-IF).** Eval artifacts now exist in-repo (`skills/code-standards/evals/evals.json`, the pilot — authored in skill-creator's CURRENT schema; its `references/schemas.md` stays the schema SSoT, never mirrored here). validate.py R7 gates the shape (skill_name=folder, unique int ids, non-empty prompt/expected_output/expectations); cases in validate_test.py; runs in the existing required gates step.
3. **Owned verdict layer — `skills/building-skills/scripts/eval_verdict.py` + test.** Post-processes upstream `benchmark.json` ONLY: pairs runs by (eval_id, run_number) across configurations; win rate with Wilson 95% CI; mean pass-rate delta; the verdict metric — **delta per 1k chars of SKILL.md body** (benefit over the enforced cost). `--fail-under` for local regression loops. Python, stdlib, in the dev-skills toolkit (ADR 0010).
4. **NOT a CI gate.** Benchmark runs are non-deterministic; gates run only `eval_verdict_test.py` (pure decision logic), never model calls (ADR 0012: gates are deterministic).
5. **Kept from the original call:** Core Principles prose stays vendored (0011 B8); author-separation — fresh Claude B writes the expectations; fresh, different-model grader on the harness path; validate.py authoritative for this repo's skills. Pressure-case authoring (method: obra/superpowers skill-testing) joins the eval disciplines in empirical-evals.md.

## Justification
Budgets cap cost; nothing measured benefit — the "justifies its cost" claim was unfalsifiable at the skill level. Upstream has the expensive machinery (executor/grader/aggregation) but not the decision layer: no confidence interval, no cost-per-context-char verdict (dollar-cost accounting was explicitly out of upstream's scope). Owning ~150 lines of pure post-processing buys the verdict without maintaining a rival harness against a moving upstream schema. LOW cost / LOW risk: stdlib, no subprocess, decision logic unit-tested.

## Assumptions
- [verified] eval artifacts exist in-repo — the pilot `skills/code-standards/evals/evals.json`; the original delegate-call's empty-road premise is gone and its REOPEN-IF resolved as planned (schema gate, not a rival loop).
- [checkable] the verdict layer's decision logic (pairing, Wilson CI, tie handling, zero-division, small-n warning) is fully covered by eval_verdict_test.py — owner: gates (python step); result: green.
- [checkable] validate.py R7 rejects each malformed shape (bad skill_name, dup ids, empty expectations, invalid JSON) and passes the pilot — owner: gates (validate_test.py); result: green.
- **[unverifiable] WEAKEST: upstream's `benchmark.json` schema stays stable enough that a pinned consumer is cheaper than an owned harness** — REOPEN-IF: an upstream schema change breaks eval_verdict.py twice in a row, or skill-creator ships CI stats + a cost verdict natively (then delete the owned layer and delegate fully).

## Rejected alternatives
- Build a full owned paired runner (spawn/grade/iterate) — re-forks upstream execution for zero marginal information; the gaps are all in the post-processing layer.
- Adopt upstream as-is, no verdict layer — leaves the owner's requirement unmet: no CI, no cost normalization, single runs read as signal.
- Mirror the evals.json schema into docs — a hand-maintained mirror drifts on the next upstream change; the gate pins shape executably, the doc points at upstream's SSoT.
- Make eval runs a CI gate — non-deterministic, un-CI-able (ADR 0012).

## Revisit triggers
- eval_verdict.py breaks on an upstream benchmark.json schema change twice in a row -> reconsider owning execution or pinning a vendored schema.
- skill-creator ships confidence intervals + a cost-per-char verdict -> delete the owned layer, delegate fully.
- skill-creator lands in this marketplace or bundles into Claude Code -> drop the conditional install pointer.
