---
id: 0025
title: "Benefit-verdict metric: fraction-met headline, not binary all-or-nothing pass"
status: accepted
summary: "The cost-justification loop (ADR 0024) read its verdict off a BINARY per-cell score (all expectations met, then survive a prosecutor). On hard multi-expectation evals that score FLOORS — both arms fail completely, the eval carries no discriminating signal, and the eval-clustered CI (ADR 0019) width-warns everywhere — which is precisely the underpowered measurement ADR 0024 says does not count. This refines the metric: the HEADLINE is fraction-met (met/total of a cell's expectations), a continuous score that sees a skill move a cell 2/5 -> 4/5 the binary metric cannot; the KEEP bar (CI excludes 0 and positive) is unchanged. Safeguard: the ADR 0019 prosecutor is applied UNIFORMLY to every cell's met-count (met_final = min(grader, prosecutor)), not just to binary passes, so partial credit gets the same adversarial scrutiny. Binary all-met is retained as a secondary diagnostic (the 'full success' view), not the headline."
---

# 0025 — benefit-verdict metric: fraction-met over binary pass

- Date: 2026-07-09
- Owner: PM (chose fraction-met + uniform-prosecutor from a 3-option panel, given the floor evidence)
- Panel: owner-decided; grounded in the skills hermetic grid (144 cells), both metrics recomputed on the same graded data. Check: `aggregate.py` emits both; the floor and the sign of the fraction-met CI were reproduced against the committed `graded/verdicts.json`.
- Context: ADR 0024 charges an artifact's benefit against its no-treatment baseline via the ADR 0019 eval-clustered CI, but left the per-cell SCORE unspecified; the first implementation used binary all-expectations-met. On the skills grid that binary score passed only 21/144 cells — most evals scored 0/0 in BOTH arms (too hard to fully satisfy single-shot), so they contributed no signal and every skill fired the <4-non-tied width warning. The measurement, not the artifacts, was underpowered.

## Decision
1. **Headline = fraction-met.** Each cell scores met/total of its eval's expectations (continuous in [0,1]). The verdict is the eval-clustered mean delta (with - without) + 95% CI (ADR 0019); the KEEP bar is unchanged (CI excludes 0 and positive, ADR 0024). Rationale: the binary all-or-nothing score floors on hard multi-expectation evals and discards a real marginal effect; the continuous score is the powered measure of the same benefit.
2. **Uniform prosecutor safeguard.** The ADR 0019 adversarial prosecutor is run on EVERY cell's met-count, not only on binary passes; met_final = min(grader_met, prosecutor_met) (the prosecutor can only reduce credit). This gives partial credit the same anti-inflation scrutiny the binary PASS already got, closing the gap where a lenient single grader's partial counts would go unchallenged.
3. **Binary all-met retained as a SECONDARY diagnostic.** The "did the task fully succeed" view is still computed and reported, but it is not the headline and does not gate the verdict.

## Justification
Fixing the metric is a MEASUREMENT iteration ADR 0024 explicitly permits, not a re-litigation of the KEEP bar. Evidence it was the metric: same 144 graded cells, binary overall +0.042 (CI straddles 0, CUT-CANDIDATE, all skills width-warned) vs fraction-met overall +0.088, 95% CI [+0.019, +0.156] (KEEP). The uniform prosecutor RAISED the fraction-met delta (+0.075 -> +0.088) by shaving the baseline's inflated partial credit hardest, so the result survives adversarial scrutiny rather than depending on grader leniency. Cost is a one-line aggregation change plus one extra grading pass; both are owned.

## Assumptions
- [checkable] both metrics are computed from the same graded data and the floor is real — `aggregate.py` on the committed grid emits binary (21/144 pass, overall CUT-CANDIDATE) and fraction-met (overall KEEP, CI excludes 0); owner: `aggregate.py` + `graded/verdicts.json`.
- [verified] the uniform prosecutor is conservative, not favorable — it reduced met on 13/144 cells and did not lift the without-arm above the with-arm on any eval; the delta moved up, not down.
- [unverifiable] WEAKEST: fraction-met is not gamed by verbose responses that tick trivial expectations while missing the load-bearing one — REOPEN-IF a sampled with-arm win traces to trivial-expectation inflation; then weight expectations or gate on the load-bearing one.

## Rejected alternatives
- Keep binary all-met as the headline — floors on hard multi-expectation evals (21/144), discarding the marginal effect the loop exists to detect; the width warnings were the instrument flagging its own underpowering.
- Fraction-met WITHOUT the uniform prosecutor — partial credit would escape the adversarial pass the binary PASS received; asymmetric rigor between the metrics.
- Require BOTH binary and fraction-met to clear — reinstates the floor as a veto and slows every verdict; the owner chose fraction-met primary with binary as diagnostic.

## Revisit triggers
- A fraction-met win is traced to trivial-expectation inflation -> weight expectations by load-bearingness, or gate on the decisive one.
- An eval set is authored with a single expectation per eval (fraction-met == binary) -> the distinction is moot there; note it in that snapshot rather than claiming a metric difference.
- A non-Claude / human grade diverges on the met-counts -> discount the Claude-only counts per ADR 0019's family-bias trigger.
