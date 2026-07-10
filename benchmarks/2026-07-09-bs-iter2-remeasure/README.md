# 2026-07-09 building-skills iteration 2 — VERDICT: NO MERGE (recorded null)

Issue #77's building-skills half: hermetic re-measure of the `bs-iter2` draft (134e6fb — a 187-char
closed-set trigger-openers clause targeting the 0/9 "description STARTS with a trigger" failures).
Arm pattern and bar: ADR 0027 via ADR 0024 step 2d; run parameters: `metadata.json`; per-eval
numbers: `results.jsonl`.

## Result (fraction-met, met_final = min(grader, prosecutor), ADR 0025)

| eval | without | with-old | with-new | d_old | d_new | diff |
|------|---------|----------|----------|-------|-------|------|
| 1 | 0.44 | 0.56 | 0.61 | +0.11 | +0.17 | +0.06 |
| 2 | 0.61 | 0.83 | 0.50 | +0.22 | -0.11 | -0.33 |
| 3 | 0.67 | 0.73 | 0.80 | +0.07 | +0.13 | +0.07 |
| 4 | 0.33 | 0.83 | 0.89 | +0.50 | +0.56 | +0.06 |
| 5 | 0.50 | 0.44 | 0.61 | -0.06 | +0.11 | +0.17 |
| 6 | 0.13 | 0.80 | 0.80 | +0.67 | +0.67 | 0.00 |

- `diff` mean **+0.002** CI [-0.137, +0.140] at **+187 always-loaded chars** — benefit flat, cost
  up, so benefit-per-token FELL: ADR 0024 step 2d reverts the edit. (`aggregate.py` prints
  "MERGE (weak)" because it encodes only the directional half of ADR 0027's amended bar; that bar's
  weak-confidence merge was explicitly contingent on the cost prong clearing, which it does not.)
- The clause failed its specific aim: grader evidence still shows "Use before" / capability-first
  descriptions across ALL arms (eval 4's expectation 2 and eval 5's expectation 6 unmoved) — an
  in-body vocabulary list does not override the model's phrasing instinct at this size.
- Eval 2's -0.33 is within single-rep noise range at n=3 (the same bimodal variance class the
  code-standards eval-1 investigation documented) — recorded, not acted on.
- Validity: d_old (+0.252, CI excludes 0) reconfirms iteration 1's merged skill against fresh
  sampling — the KEEP survives replication.

Iteration ledger (ADR 0024 plateau rule): building-skills iteration 1 = marginal keep (+0.009);
iteration 2 = this null. One more no-gain iteration triggers the cut-is-fallback path.

## Reproduce

```bash
python prep.py                                   # treatments (old=checkout, new=git show 134e6fb); asserts touched set
HERMETIC_RELOCATE_USER_MEMORY=1 bash harness.sh  # 54 cells -> outputs/   (verify ~/.claude/CLAUDE.md symlink after)
python blind.py
# Workflow ../2026-07-08-skills-hermetic/grade.workflow.js            {itemsDir, bids} -> graded/verdicts.jsonl
# Workflow ../2026-07-08-skills-hermetic/prosecute_counts.workflow.js {itemsDir, bids} -> graded/prosecute_counts.jsonl
python aggregate.py
python archive_raw.py
```
