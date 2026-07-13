---
name: bench-verdict
description: Use when re-running the verdict math on an existing graded skill-bench benchmark dir with a pluggable judge and no new generation spend: (a) recompute KEEP/CUT with a cross-family judge (grok default), or (b) run --judge both for the judge-divergence diagnostic (agreement, kappa, verdict flip) that quantifies same-family judge bias. Invoke explicitly; never model-invoked.
disable-model-invocation: true
---

# /bench-verdict

Recompute a decision-outcome benchmark's verdict from its already-graded, blinded, normalized cells —
swapping only the JUDGE. No new arms are generated, so there is no generation spend; the only cost is
the judge calls (grok is subscription-billed = zero marginal cost).

## Why this exists

A same-family judge (Claude grading Claude) is a measured confound, not a theoretical one. On #172's
Instrument 2, swapping opus -> grok-4.5 moved the panel-vs-cost-matched verdict from +0.010 (null) to
+0.125 (KEEP-leaning) and cut the overall met-rate ~20pp. The judge is a first-class variable, so it is
reported, and `--judge both` surfaces the divergence instead of hiding it.

## Usage

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bench_verdict.py" --dir <benchmark-dir> --judge grok|claude|both [--out report.json]
```

(Invoke via `${CLAUDE_PLUGIN_ROOT}` so the script resolves no matter the working directory when installed as a plugin.)

- `--dir` must contain `graded/{verdicts.jsonl,arm_map.tsv,keys.json}` (ADR 0025/0026 layout).
- `--judge grok` (default): re-grade with grok-4.5 (grade + prosecute), emit arm means, clustered
  C-B with 95% CI (ADR 0019), KEEP/CUT verdict, per-expectation rates.
- `--judge both`: also load the committed baseline judge and emit `divergence` (agreement, Cohen's
  kappa, stricter-count, per-judge met-rate) and `verdict_flip` (did KEEP/CUT direction change).
- `--cache <regrade.jsonl>`: reuse a prior judge run offline (no calls) — for re-analysis / CI.

## Guardrails

- Normalization is REUSED from the committed cells (the only stage that sees raw output), so the judge
  family is the sole changed variable — the swap is a clean measurement, not a prompt-difference.
- Read-only on the benchmark dir; writes only to `--out`. Never edits a frozen dated dir (ADR 0026).
- Judge backends deny all file/shell/web tools (pure-text grading). grok known-good deny set only
  (a longer list trips a grok 0.2.99 tool-config bug).

## Caveat it must print

n is small (scenario-clustered, typically 8 clusters): CIs are wide, verdicts are exploratory. A judge
flip is a signal to re-measure, not a settled result. Normalization remains same-family until a
cross-family normalizer ships (ADR 0055 weakest assumption).
