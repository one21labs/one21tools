---
id: 0019
title: "Eval verdict layer: clustered CI, honest denominator, sequential replicates, blind grading"
status: accepted
summary: "Six corrections to the owned verdict layer (eval_verdict.py + protocol), from a 432-run grid and its bias audit: (1) headline Wilson CI clusters replicates per eval (correlated within an eval), two-level report, warn under 4 non-tied evals; (2) sequential replicates — escalate only where the eval-level CI straddles the boundary; (3) defer Plackett-Burman ablation (unexercised path); (4) charge the delta against the FULL loaded surface (body + references, or a measured count) not body alone — reference-heavy skills were flattered ~8x; (5) blind the arm labels from the grader; (6) append-only dated JSONL result snapshots (machine-readable SSoT). Named residual: Claude-grades-Claude family bias."
---

# 0019 — eval verdict layer: statistical validity, honest denominator, unbiased grading

- Date: 2026-07-07
- Owner: PM
- Panel: items 1-3 (DoE) — opposing counsel, 2 sonnet advisors (adopt-all vs minimal/defer), unprimed; Check recomputed both [checkable] assumptions against the grid. Items 4-6 (validity) — owner-directed from the grid bias audit; Check: gates + a fresh verifier. One owned-layer concern, one record.
- Context: the grid's verdicts had validity gaps: correlated replicate pairs treated as independent; fixed replicates misallocated across decided vs ambiguous cells; the per-1k denominator ignored references/*.md (engineering-principles flattered ~8x); graders saw the arm in the path; only Claude can grade (fixed constraint); raw runs were ephemeral, so nothing was re-checkable and --fail-under had no baseline.

## Decision
1. **Eval-clustered CI (two-level report).** Keep pair-level W/L/T + mean delta as detail; the HEADLINE Wilson CI clusters replicates per eval (each eval's mean delta -> one win/loss/tie), over non-tied EVALS. Warn under 4 non-tied evals (the 4+-case authoring floor). Implemented, unit-tested.
2. **Sequential replicates.** Keep the 3-replicate minimum; escalation protocol (when to add replicates/evals) lives in `skills/building-skills/references/empirical-evals.md` ("Running the benchmark"). No owned stopping controller.
3. **Defer Plackett-Burman** for Tier 2 ablation — the path is unexercised; OFAT guidance stands. REOPEN-IF below.
4. **Honest denominator.** Charge the delta against the loaded surface: default SKILL.md body (always-on cost); `--include-references` adds references/*.md (upper bound); `--loaded-chars N` takes a measured count and wins. The report labels the basis; report BOTH bounds for reference-heavy skills. Implemented, unit-tested.
5. **Blind grading + family-bias mitigation stack.** Stage runs under neutral A/B labels, mapping withheld from the grader. The Claude-only grader is a fixed CONSTRAINT; pairing cancels raw self-preference; the stack (protocol owns details) attacks the rest: mechanize-first assertions (executable checks carry no family bias), planted-defect calibration, a prosecutor pass on PASSes, and a periodic human calibration sample (the one external anchor). Residual: judgment-only assertions stay directional — bounded, not eliminated.
6. **Durable snapshots — JSON/JSONL, not markdown.** Append a dated `.jsonl` of verdict records + `metadata.json` under `benchmarks/` per run (executor model, eval-set hash, protocol version, blinded y/n, denominator basis); markdown is rendered from the JSON, never hand-kept. Append-only; a record as-of-date, not a live mirror.

## Justification
Each item removes a known-direction bias (denominator + unblinded grader: skill-favorable; independent-pairs CI: overconfident) or unblocks verification, all inside the layer ADR 0013 says this repo OWNS — fix the instrument, don't caveat it. Cost low: pure unit-tested logic; the rest is protocol text.

## Assumptions
- [verified] zero direction flips under eval-level clustering across all 12 grid cells (orchestrator recompute); the blanket eval-level warning is a threshold artifact, not lost signal (building-skills clustered CI 0.61-1.00 all tiers).
- [verified] the denominator effect is real and large — engineering-principles +0.0235 body-only vs +0.0029 body+references (~8x); low-reference skills barely move.
- [checkable] clustering, denominator precedence, the two-level report, and the eval-level warning are covered by eval_verdict_test.py — owner: gates (python step); result: green.
- [unverifiable] WEAKEST: blinding materially changes a verdict vs the unblinded grid — REOPEN-IF a blinded re-grade of a grid sample flips a cell's direction; else the historicals stand.
- [unverifiable] family self-preference does not dominate the deltas — REOPEN-IF a non-Claude or human grade on one skill diverges materially; then discount Claude-only verdicts.

## Rejected alternatives
- Prose caveat instead of fixing the CI/denominator — guards a miscalibrated instrument; the ~8x gap and correlated-pairs overconfidence are too large to leave in ranked numbers.
- Eval-level CI only (drop pair-level detail) — cuts the per-eval deltas the iteration flags need.
- References as always-on (fold into body) — overcounts rarely-loaded refs; two-bound + measured is more honest.
- Plackett-Burman / a code stopping-rule / a non-Claude grader now — machinery ahead of demand; each behind a trigger.

## Revisit triggers
- A blinded re-grade flips any grid cell -> re-benchmark that skill blinded, supersede the verdict.
- A non-Claude/human spot-check diverges materially -> discount Claude-only verdicts; weigh a second-family grader.
- A skill needs Tier 2 with >3 sections under doubt -> reopen Plackett-Burman.
- A sequentially-stopped cell flips on added data -> reopen the stopping rule.
- `benchmarks/` snapshots bloat the repo -> move to a data branch / release assets.
- skill-creator ships clustered CIs + a cost verdict natively -> ADR 0013's delete-the-owned-layer trigger applies.
