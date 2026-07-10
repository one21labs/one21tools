---
id: 0035
title: "tiered-agent execution verdict: do not adopt per-task orchestration; tier by work type"
status: accepted
summary: "Issue #41 measured (benchmarks/2026-07-10-tiered-execution-fullgrid, pre-registered bar): tiered (sonnet plans/validates, haiku implements, <=2 iterations) fails the cost/time gate outright — 2.94x tokens, 3.22x wall-clock vs sonnet-solo against a <=0.6x bar — with judged quality -0.057 (below the -0.05 margin, CI straddling). Haiku-solo is 0.36x cost but judged-quality -0.160 (CI excludes zero): haiku matches sonnet on mechanized/structural expectations (0.412 vs 0.424) and loses on judgment. DO NOT codify a haiku implementer tier into pdca-workflow's Do phase; ADR 0006's split stands, now empirically grounded: haiku mechanical-only, sonnet+ judgment."
---

# 0035 — tiered-agent execution verdict

- Date: 2026-07-10
- Owner: PM (verdict read mechanically off the pre-registered bar)
- Panel: none — the bar was pre-registered in metadata.json before any run; the verdict is arithmetic.
- Context: issue #41 proposed redesigning pdca-workflow so a top-tier model plans/orchestrates and cheaper models implement, adopted only on measurement (ADR 0024). Arms: sonnet-solo (baseline), haiku-solo, tiered (sonnet plan -> haiku implement -> sonnet validate, <=2 worker iterations, worker owns the deliverable). 24 evals x 3 arms x 3 reps, hermetic claude -p executor (ADR 0023; clean config dir + empty cwd + tool deny), real per-cell tokens/cost/duration from the CLI JSON envelope. Quality graded blind + uniform prosecutor (ADR 0025) on the 8-task gradient subset (amendment recorded pre-unblinding; the parallel #41 run's pre-screen showed most of the battery floors on model-tier comparisons).

## Decision
1. **Do not adopt tiered per-task orchestration.** It failed the pre-registered gate: tokens 2.94x and wall-clock 3.22x of sonnet-solo (bar: <=0.6x either), judged quality -0.057 (bar: > -0.05). The plan+validate overhead (two extra sonnet calls per cell) exceeds the haiku savings at this task granularity; the loop does raise quality over haiku-solo (+0.10) but costs 6.2x haiku and 2.3x sonnet-solo for slightly-below-sonnet output.
2. **Do not adopt haiku-solo as a general implementer.** 0.36x cost but judged quality -0.160 vs sonnet-solo, CI [-0.279, -0.041] excludes zero. The two grading instruments split cleanly: haiku matches sonnet on mechanized/structural expectations (0.412 vs 0.424) and loses on judgment-heavy ones — form holds, substance does not.
3. **ADR 0006's model split stands, now with empirical grounding, and extends as doctrine:** haiku for mechanical execution only (format conversions, mechanical sweeps, structure-bound output); sonnet and above wherever judgment is the work product. No pdca-workflow plugin change; no worker/implementer agent is added.
4. Record both runs as append-only snapshots: this full grid (benchmarks/2026-07-10-tiered-execution-fullgrid/) and the parallel session's pre-screened gradient run (branch claude/issue-41-8awnsc) as an independent replication-in-flight.

## Justification
The bar was written before any cell ran; every number above is from committed artifacts (outputs/*.summary.json, graded/verdicts.jsonl + prosecute_counts.jsonl, results.jsonl). ADR 0024: adopt only what measurably earns its cost — neither configuration does.

## Assumptions
- [checkable] the cost/time ratios reproduce from the committed summaries — owner: gate; result: verified 2026-07-10 (aggregate.py recomputes 2.935/3.22/2.272 from outputs/*.summary.json).
- [unverifiable] per-task orchestration could pay at LARGER task granularity (multi-file implementation work), where one plan amortizes over more worker output — this run's single-shot text tasks are the pessimal case. REOPEN-IF a real multi-file workload shows tiered <=0.6x cost at non-inferior quality.
- [checkable] the parallel run (claude/issue-41-8awnsc) reaches a compatible verdict — owner: whoever lands that branch; result: pending (named signal: that branch's PR).

## Rejected alternatives
- Adopt tiered for quality (it scored +0.10 over haiku-solo, +0.035 over sonnet on 3 tasks) — the issue's premise was cost/time efficiency; paying 2.3x for -0.057 quality is the opposite.
- Difficulty-adjust the bar post-hoc — the bar predates the run; moving it after unblinding is the exact failure ADR 0024 D3 forbids.
- Grade the full 24-task battery for a stronger CI — most non-gradient tasks floor on model-tier comparison (parallel run's pre-screen); grading ties adds cost, not signal (pre-screen rule, empirical-evals.md).

## Revisit triggers
- The parallel #41 run's verdict contradicts this one -> reconcile before either is cited as settled.
- A multi-file/agentic workload benchmark becomes runnable -> re-test tiered at that granularity (the [unverifiable] above).
- Haiku-tier pricing or capability shifts materially -> re-run haiku-solo vs sonnet-solo on the gradient subset.
