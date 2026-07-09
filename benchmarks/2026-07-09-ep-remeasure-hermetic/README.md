# 2026-07-09 EP re-measure — VERDICT: MERGE (weak-confidence, cost prong strong)

Issue #52: hermetic re-measure of the `engineering-principles` improvement draft (675033c) vs
main, first end-to-end test of the ADR 0024 improvement loop. Arm construction, merge bar, and
escalation rule are owned by **ADR 0027** (decided and amended before results were seen); run
parameters by `metadata.json`; per-eval numbers by `results.jsonl`. This file only summarizes.

## Result (fraction-met, met_final = min(grader, prosecutor), ADR 0025)

| eval | without | with-old | with-new | d_old | d_new | diff |
|------|---------|----------|----------|-------|-------|------|
| 1 | 0.83 | 1.00 | 1.00 | +0.17 | +0.17 | 0.00 |
| 2 | 0.80 | 0.80 | 1.00 | 0.00 | +0.20 | +0.20 |
| 3 | 0.78 | 0.67 | 0.78 | -0.11 | 0.00 | +0.11 |
| 4 | 0.60 | 0.60 | 0.67 | 0.00 | +0.07 | +0.07 |
| 5 | 0.20 | 0.13 | 0.80 | -0.07 | +0.60 | +0.67 |
| 6 | 0.20 | 0.40 | 0.40 | +0.20 | +0.20 | 0.00 |

- `d_old` mean +0.031, CI [-0.069, +0.132] — reproduces the recorded +0.020 baseline in-run
  (instrument consistency).
- `d_new` mean +0.206, CI [+0.038, +0.373] — the improved skill's benefit excludes 0.
- `diff` mean +0.174, CI [-0.028, +0.376] — MERGE per ADR 0027's directional bar,
  weak-confidence (CI straddles); no eval regressed (all diffs >= 0).
- Cost: body 5464 -> 4012 chars (-1452 always-loaded); full treatment +39 (~neutral).
- Option E escalation does NOT fire (`d_new` > 0 on all of evals 1/2/5/6).
- Eval 5 moved as the diagnosis predicted (0.13 -> 0.80): the "already approved" design-review
  trigger fix was the highest-ceiling edit.

## Reproduce

```bash
python prep.py                                   # treatments (old=checkout, new=git show 675033c), prompts, cells, meta
HERMETIC_RELOCATE_USER_MEMORY=1 bash harness.sh  # 54 cells -> outputs/   (verify ~/.claude/CLAUDE.md symlink after)
python blind.py                                  # outputs/ -> graded/items (arm withheld) + arm_map.tsv
# Workflow ../2026-07-08-skills-hermetic/grade.workflow.js            {itemsDir, bids} -> graded/verdicts.jsonl
# Workflow ../2026-07-08-skills-hermetic/prosecute_counts.workflow.js {itemsDir, bids} -> graded/prosecute_counts.jsonl
python aggregate.py                              # -> results.jsonl + verdict
python archive_raw.py                            # once: outputs/all.tar.gz + per-(eval,arm) sample
```
