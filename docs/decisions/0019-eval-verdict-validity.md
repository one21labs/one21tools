---
id: 0019
title: "Eval verdict layer: clustered CI, honest denominator, sequential replicates, blind grading"
status: accepted
summary: "Six corrections to the owned verdict layer (eval_verdict.py + protocol), from a 432-run grid and its bias audit: eval-clustered headline CI, sequential replicates, deferred Plackett-Burman, an honest denominator (reference-heavy skills were flattered ~8x), blind grading, and append-only JSONL snapshots. Named residual: Claude-grades-Claude family bias."
---

# 0019 — eval verdict layer: statistical validity, honest denominator, unbiased grading

- Date: 2026-07-07
- Owner: PM
- Context: a 432-run grid's bias audit found the validity gaps each decision below closes.

## Decision
1. **Eval-clustered CI (two-level report).** Keep pair-level W/L/T + mean delta as detail; the HEADLINE Wilson CI clusters replicates per eval, over non-tied evals. Warn under 4 non-tied evals.
2. **Sequential replicates.** Keep the 3-replicate minimum; escalation protocol lives in `skill-bench/skills/bench/references/empirical-evals.md`.
3. **Defer Plackett-Burman** for Tier-2 ablation — unexercised path; OFAT guidance stands.
4. **Honest denominator.** Charge the delta against the loaded surface: default SKILL.md body; `--include-references` adds references/*.md; `--loaded-chars N` (measured) wins.
5. **Blind grading + family-bias mitigation stack.** Neutral A/B labels, mapping withheld from the grader. The Claude-only grader is a fixed constraint; the mitigation stack attacks the rest. Residual: judgment-only assertions stay directional.
6. **Durable snapshots — JSON/JSONL, not markdown.** Append-only, dated `.jsonl` + `metadata.json` under `benchmarks/` per run; markdown is rendered from the JSON, never hand-kept.

## Justification
Each item removes a known-direction bias (denominator + unblinded grader: skill-favorable; independent-pairs CI: overconfident), inside the layer this repo owns.

## Assumptions
- [verified] zero direction flips under eval-level clustering across all 12 grid cells; the denominator effect is real and large (~8x for a reference-heavy skill).
- [checkable] clustering, denominator precedence, the two-level report, and the eval-level warning are covered by `eval_verdict_test.py`. result: green.
- [unverifiable] WEAKEST: blinding materially changes a verdict vs the unblinded grid — REOPEN-IF a blinded re-grade of a grid sample flips a cell's direction.
- [unverifiable] family self-preference does not dominate the deltas — REOPEN-IF a non-Claude or human grade diverges materially.

## Rejected alternatives
- A prose caveat instead of fixing the CI/denominator; eval-level CI only (cuts per-eval deltas); references as always-on (overcounts rarely-loaded refs); Plackett-Burman/a non-Claude grader now — machinery ahead of demand.

## Revisit triggers
- A blinded re-grade flips any grid cell -> re-benchmark that skill blinded, supersede the verdict.
- A non-Claude/human spot-check diverges materially -> discount Claude-only verdicts.
- A skill needs Tier 2 with >3 sections under doubt -> reopen Plackett-Burman; `benchmarks/` snapshots bloat the repo -> move to a data branch.
